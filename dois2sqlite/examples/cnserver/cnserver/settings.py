SUPPORTED_FORMATS = [
    {'format': 'Commonmeta', 'name': 'commonmeta', 'content_type': 'application/vnd.commonmeta+json', 'read': 'yes', 'write': 'yes'},
    {'format': 'CrossRef XML', 'name': 'crossref_xml', 'content_type': 'application/vnd.crossref.unixref+xml', 'read': 'yes', 'write': 'yes'},
    {'format': 'Crossref', 'name': 'crossref', 'content_type': 'application/vnd.crossref+json', 'read': 'yes', 'write': 'n/a'},
    {'format': 'DataCite', 'name': 'datacite', 'content_type': 'application/vnd.datacite.datacite+json', 'read': 'yes', 'write': 'yes'},
    {'format': 'Schema.org (in JSON-LD)', 'name': 'schema_org', 'content_type': 'application/vnd.schemaorg.ld+json', 'read': 'yes', 'write': 'yes'},
    {'format': 'RDF XML', 'name': 'rdf_xml', 'content_type': 'application/rdf+xml', 'read': 'no', 'write': 'later'},
    {'format': 'RDF Turtle', 'name': 'turtle', 'content_type': 'text/turtle', 'read': 'no', 'write': 'later'},
    {'format': 'CSL-JSON', 'name': 'csl', 'content_type': 'application/vnd.citationstyles.csl+json', 'read': 'yes', 'write': 'yes'},
    {'format': 'Formatted text citation', 'name': 'citation', 'content_type': 'text/x-bibliography', 'read': 'n/a', 'write': 'yes'},
    {'format': 'Codemeta', 'name': 'codemeta', 'content_type': 'application/vnd.codemeta.ld+json', 'read': 'yes', 'write': 'later'},
    {'format': 'Citation File Format (CFF)', 'name': 'cff', 'content_type': 'application/vnd.cff+yaml', 'read': 'yes', 'write': 'later'},
    {'format': 'JATS', 'name': 'jats', 'content_type': 'application/vnd.jats+xml', 'read': 'later', 'write': 'later'},
    {'format': 'CSV', 'name': 'csv', 'content_type': 'text/csv', 'read': 'no', 'write': 'later'},
    {'format': 'BibTex', 'name': 'bibtex', 'content_type': 'application/x-bibtex', 'read': 'later', 'write': 'yes'},
    {'format': 'RIS', 'name': 'ris', 'content_type': 'application/x-research-info-systems', 'read': 'yes', 'write': 'yes'},
    {'format': 'InvenioRDM', 'name': 'inveniordm', 'content_type': 'application/vnd.inveniordm.v1+json', 'read': 'later', 'write': 'yes'},
    {'format': 'JSON Feed', 'name': 'json_feed_item', 'content_type': 'application/feed+json', 'read': 'yes', 'write': 'later'}
]

SUPPORTED_WRITE_FORMATS = [f for f in SUPPORTED_FORMATS if f['write'] == 'yes']
MEDIA_TYPE_TO_NAME = {media_type['content_type']: media_type['name'] for media_type in SUPPORTED_FORMATS}
SUPPORTED_MEDIA_TYPES = [media_type['content_type'] for media_type in SUPPORTED_WRITE_FORMATS]

