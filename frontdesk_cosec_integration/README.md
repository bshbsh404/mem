# Frontdesk COSEC Integration

This module integrates the Frontdesk system with COSEC access control system.

## Features

- Automatic sending of visitor data (emp_id and qr_string) to COSEC system when a new visit is created
- Configurable API settings for COSEC integration
- Comprehensive logging of all API calls
- Manual retry functionality for failed requests
- Station-specific configuration
- Test connection functionality

## Installation

1. Install the module in Odoo
2. Go to Frontdesk > COSEC Integration > Configuration
3. Create or edit the COSEC configuration with your API details

## Configuration

### API Settings
- **API URL**: `https://acixsupport.dvrdns.org:446/COSEC/api.svc/v2/user`
- **Username**: `nama`
- **Password**: `Admin@123`
- **Employee ID Prefix**: `NAMA` (will be added before emp_id)

### URL Format
The module sends data using the following URL format:
```
https://acixsupport.dvrdns.org:446/COSEC/api.svc/v2/user?action=set;id=NAMA{emp_id};active=0
```

### Response Format
Expected response from COSEC:
```
1 success: 0070200001 : saved successfully. User ID = NAMA{emp_id}
```

## Usage

### Automatic Integration
When a new visitor is created, the system automatically:
1. Extracts emp_id and qr_string from the visitor record
2. Sends data to COSEC API
3. Logs the request and response
4. Updates visitor record with COSEC status

### Manual Actions
- **Send to COSEC**: Manual button to resend visitor data
- **Retry**: Retry failed COSEC requests
- **Test Connection**: Test API connectivity

### Monitoring
- View all COSEC logs in Frontdesk > COSEC Integration > Logs
- Monitor success/failure rates
- Debug API issues

## API Endpoints

### Send Visitor Data
```
POST /frontdesk/cosec/send_visitor_data
{
    "visitor_id": 123
}
```

### Test Connection
```
POST /frontdesk/cosec/test_connection
```

### Get Logs
```
POST /frontdesk/cosec/get_logs
{
    "visitor_id": 123,
    "limit": 50
}
```

## Troubleshooting

1. **Connection Issues**: Use "Test Connection" button
2. **Failed Requests**: Check logs for error details
3. **Authentication**: Verify username/password in configuration
4. **SSL Issues**: Module uses `verify=False` for self-signed certificates

## Security

- Passwords are stored encrypted in the database
- API calls use Basic Authentication
- All requests are logged for audit purposes
- Station-specific access control






