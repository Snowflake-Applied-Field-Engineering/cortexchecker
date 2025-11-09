# Setup Guide Fixes

## Issues Addressed

Based on user feedback, the following issues have been fixed in the setup documentation:

### 1. Missing Warehouse Creation

**Issue:** The setup assumed `COMPUTE_WH` warehouse already exists.

**Fix:** Added warehouse creation step:
```sql
CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH
  WITH WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;
```

### 2. CURRENT_USER() Function Issue

**Issue:** The statement `GRANT ROLE CORTEX_ADMIN TO USER IDENTIFIER(CURRENT_USER());` doesn't work in a worksheet because `CURRENT_USER()` is a function and cannot be used with `IDENTIFIER()`.

**Fix:** Changed to:
```sql
-- Grant role to your user (replace <YOUR_USERNAME> with your actual username)
GRANT ROLE CORTEX_ADMIN TO USER <YOUR_USERNAME>;
```

**Alternative:** Users can run this separately without IDENTIFIER:
```sql
GRANT ROLE CORTEX_ADMIN TO USER CURRENT_USER();
```

## Files Updated

- ✅ `README.md` - Quick Start section
- ✅ `SETUP_GUIDE.md` - Complete setup instructions

## Testing in Snowsight

The app is designed to be deployed as a Streamlit in Snowflake application. To test:

1. Follow the setup instructions in `SETUP_GUIDE.md`
2. Deploy via **Projects → Streamlit** in Snowsight
3. Configure with:
   - Location: `CORTEX_TOOLS.APPS`
   - Warehouse: `COMPUTE_WH`
   - Role: `CORTEX_ADMIN`

This ensures the app runs with the proper permissions and context within Snowflake.

## Additional Notes

- The warehouse size `XSMALL` is sufficient for the app's operations
- Auto-suspend is set to 60 seconds to minimize costs
- Users should replace `<YOUR_USERNAME>` with their actual Snowflake username
- For scripted deployments, consider using a variable or parameter for the username

