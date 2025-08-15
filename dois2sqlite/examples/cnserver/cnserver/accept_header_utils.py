def parse_accept_header(header):
    """
    Parse an HTTP Accept header into a structured Python object.

    :param header: An HTTP Accept header string.
    :return: A list of dictionaries, each representing a media type and its parameters.
    """
    # Split the header into media type specifications
    media_types = header.split(',')

    # Initialize an empty list to hold parsed media types
    parsed_media_types = []

    for media_type in media_types:
        # Trim whitespace
        media_type = media_type.strip()

        # Split media type from its parameters (if any)
        parts = media_type.split(';')

        # The first part is always the media type
        type_part = parts[0].strip()
        parameters = {}

        # Process optional parameters, if present
        for param in parts[1:]:
            key, value = param.strip().split('=')
            parameters[key.strip()] = value.strip()

        # Add the media type and its parameters to the list
        parsed_media_types.append({'media_type': type_part, 'parameters': parameters})

        # sort the list by q value
        parsed_media_types.sort(key=lambda x: float(x['parameters'].get('q', 1)), reverse=True)

    return parsed_media_types

# Example usage
# header = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
# parsed_header = parse_accept_header(header)
# print(parsed_header)
