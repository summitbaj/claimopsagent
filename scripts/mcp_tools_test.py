from app.dataverse.mcp_tools import execute_sql_query, fetch_dataverse_record

CLAIM_ID = '98646d2d-78b4-f011-bbd3-6045bd02007a'

print('Running execute_sql_query...')
sql = f"SELECT TOP 1 smvs_claimid, smvs_name, createdon FROM smvs_claims WHERE smvs_claimid = '{CLAIM_ID}';"
res = execute_sql_query(sql)
print('SQL Result:\n', res)

print('\nRunning fetch_dataverse_record...')
res2 = fetch_dataverse_record('smvs_claims', CLAIM_ID)
print('Fetch Result:\n', res2)
