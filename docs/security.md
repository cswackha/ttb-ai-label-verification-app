# Security Considerations

This prototype may send uploaded label artwork to OpenAI for assessment purposes. A production version should use an agency-approved environment, approved model endpoint, authentication, authorization, audit logging, retention controls, encryption, monitoring, and security review before handling sensitive or non-public application data.

## Current Controls

- No hardcoded API keys
- Environment-based configuration
- No sensitive data required
- No persistent storage of submitted data
- Human-in-the-loop recommendations
- Basic input validation

## Future Production Enhancements

- CSV upload for application records.
- Field-of-vision checks for distilled spirits.
- Confidence scoring per extracted field.
- Audit trail and reviewer sign-off.
- Role-based access control.
- Integration with COLA Online or internal workflow systems.
- Agency-hosted OCR/model endpoint.