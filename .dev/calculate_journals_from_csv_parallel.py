#!/usr/bin/env python3
"""
Calculate impact factors from CSV in parallel using multiple processes
"""

import sys
import os
import csv
import subprocess
from pathlib import Path
from multiprocessing import Pool, cpu_count
from functools import partial
import time

def calculate_journal_if(journal_data, year, impact_factor_script):
    """Calculate IF for a single journal"""
    name = journal_data['journal_name']
    issn = journal_data['issn']

    start_time = time.time()

    cmd = [
        "python",
        str(impact_factor_script),
        "--issn", issn,
        "--year", year,
        "--method", "reference-graph"  # Use accurate year-specific citations
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per journal
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            # Parse IF from output
            for line in result.stdout.split('\n'):
                if "Impact Factor:" in line:
                    if_value = line.split("Impact Factor:")[-1].strip()
                    return {
                        'journal': name,
                        'issn': issn,
                        'target_year': year,
                        'impact_factor': if_value,
                        'status': 'success',
                        'time': f"{elapsed:.1f}s"
                    }

            return {
                'journal': name,
                'issn': issn,
                'target_year': year,
                'impact_factor': 'N/A',
                'status': 'parse_error',
                'time': f"{elapsed:.1f}s"
            }
        else:
            error_msg = result.stderr[:100] if result.stderr else "Unknown error"
            return {
                'journal': name,
                'issn': issn,
                'target_year': year,
                'impact_factor': 'N/A',
                'status': f'error: {error_msg}',
                'time': f"{elapsed:.1f}s"
            }

    except subprocess.TimeoutExpired:
        return {
            'journal': name,
            'issn': issn,
            'target_year': year,
            'impact_factor': 'N/A',
            'status': 'timeout',
            'time': '300s+'
        }
    except Exception as e:
        return {
            'journal': name,
            'issn': issn,
            'target_year': year,
            'impact_factor': 'N/A',
            'status': f'exception: {str(e)}',
            'time': 'N/A'
        }

def main():
    script_dir = Path(__file__).parent
    csv_file = script_dir / "major_journals_with_issn.csv"
    output_dir = script_dir / "results"
    output_dir.mkdir(exist_ok=True)

    year = sys.argv[1] if len(sys.argv) > 1 else "2023"
    num_workers = int(sys.argv[2]) if len(sys.argv) > 2 else min(8, cpu_count())

    output_file = output_dir / f"major_journals_IF_{year}_parallel.csv"
    impact_factor_script = script_dir.parent / "impact_factor" / "calculate_if.py"

    print("="*60)
    print("Calculating Impact Factors (PARALLEL)")
    print("="*60)
    print(f"Year: {year}")
    print(f"Workers: {num_workers} (CPU cores: {cpu_count()})")
    print(f"Input: {csv_file}")
    print(f"Output: {output_file}")
    print()

    # Read journals
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        journals = list(reader)

    print(f"Found {len(journals)} journals with ISSNs")
    print(f"Estimated time: {len(journals) * 30 / num_workers / 60:.1f} minutes")
    print()
    print("Starting parallel processing...")
    print("-"*60)

    start_time = time.time()

    # Create a partial function with fixed arguments
    calculate_func = partial(
        calculate_journal_if,
        year=year,
        impact_factor_script=impact_factor_script
    )

    # Process in parallel
    with Pool(processes=num_workers) as pool:
        results = []
        for i, result in enumerate(pool.imap(calculate_func, journals), 1):
            results.append(result)

            status_icon = "✓" if result['status'] == 'success' else "✗"
            if_display = result['impact_factor'] if result['status'] == 'success' else result['status']

            print(f"[{i:2d}/{len(journals)}] {status_icon} {result['journal']:40s} IF={if_display:>10s} ({result['time']})")

    elapsed_total = time.time() - start_time

    # Write results
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['journal', 'issn', 'target_year', 'impact_factor', 'status', 'time'])
        writer.writeheader()
        writer.writerows(results)

    print("-"*60)
    print("="*60)
    print("Complete!")
    print("="*60)
    print(f"Total time: {elapsed_total/60:.1f} minutes")
    print(f"Results saved to: {output_file}")
    print()

    # Summary
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"Successful: {success_count}/{len(journals)}")

    if success_count > 0:
        print(f"\nTop 10 by Impact Factor:")
        print("-"*60)
        sorted_results = sorted(
            [r for r in results if r['status'] == 'success'],
            key=lambda x: float(x['impact_factor'].split()[0]),
            reverse=True
        )[:10]

        for i, r in enumerate(sorted_results, 1):
            print(f"{i:2d}. {r['journal']:40s} IF = {r['impact_factor']}")

if __name__ == "__main__":
    main()
