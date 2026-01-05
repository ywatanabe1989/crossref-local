#!/usr/bin/env python3
"""
Calculate impact factors from a CSV file with journal names and ISSNs
"""

import sys
import os
import csv
import subprocess
from pathlib import Path

def main():
    script_dir = Path(__file__).parent
    csv_file = script_dir / "major_journals_with_issn.csv"
    output_dir = script_dir / "results"
    output_dir.mkdir(exist_ok=True)

    year = sys.argv[1] if len(sys.argv) > 1 else "2023"
    output_file = output_dir / f"major_journals_IF_{year}.csv"

    print("="*60)
    print("Calculating Impact Factors from CSV")
    print("="*60)
    print(f"Year: {year}")
    print(f"Input: {csv_file}")
    print(f"Output: {output_file}")
    print()

    # Read journals with ISSNs
    journals = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        journals = list(reader)

    print(f"Found {len(journals)} journals with ISSNs")
    print()

    # Calculate IF for each journal
    all_results = []

    for i, journal in enumerate(journals, 1):
        name = journal['journal_name']
        issn = journal['issn']

        print(f"[{i}/{len(journals)}] Processing: {name} (ISSN: {issn})")

        # Run calculate_if.py for this journal
        cmd = [
            "python",
            str(script_dir.parent / "impact_factor" / "calculate_if.py"),
            "--issn", issn,
            "--year", year
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per journal
            )

            # Parse the output to extract IF
            if result.returncode == 0:
                # Look for "Impact Factor: X.XXX" in output
                for line in result.stdout.split('\n'):
                    if "Impact Factor:" in line:
                        if_value = line.split("Impact Factor:")[-1].strip()
                        all_results.append({
                            'journal': name,
                            'issn': issn,
                            'target_year': year,
                            'impact_factor': if_value,
                            'status': 'success'
                        })
                        print(f"  ✓ IF = {if_value}")
                        break
                else:
                    print(f"  ⚠ Could not parse IF from output")
                    all_results.append({
                        'journal': name,
                        'issn': issn,
                        'target_year': year,
                        'impact_factor': 'N/A',
                        'status': 'parse_error'
                    })
            else:
                print(f"  ✗ Error: {result.stderr[:100]}")
                all_results.append({
                    'journal': name,
                    'issn': issn,
                    'target_year': year,
                    'impact_factor': 'N/A',
                    'status': 'error'
                })

        except subprocess.TimeoutExpired:
            print(f"  ✗ Timeout")
            all_results.append({
                'journal': name,
                'issn': issn,
                'target_year': year,
                'impact_factor': 'N/A',
                'status': 'timeout'
            })

        except Exception as e:
            print(f"  ✗ Exception: {e}")
            all_results.append({
                'journal': name,
                'issn': issn,
                'target_year': year,
                'impact_factor': 'N/A',
                'status': 'exception'
            })

        print()

    # Write results
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['journal', 'issn', 'target_year', 'impact_factor', 'status'])
        writer.writeheader()
        writer.writerows(all_results)

    print("="*60)
    print("Complete!")
    print("="*60)
    print(f"Results saved to: {output_file}")
    print()

    # Show summary
    success_count = sum(1 for r in all_results if r['status'] == 'success')
    print(f"Successful: {success_count}/{len(journals)}")

    # Show top 10 by IF
    print("\nTop 10 by Impact Factor:")
    sorted_results = sorted(
        [r for r in all_results if r['status'] == 'success'],
        key=lambda x: float(x['impact_factor'].split()[0]) if x['impact_factor'] != 'N/A' else 0,
        reverse=True
    )[:10]

    for i, r in enumerate(sorted_results, 1):
        print(f"{i:2d}. {r['journal']:40s} IF={r['impact_factor']}")

if __name__ == "__main__":
    main()
