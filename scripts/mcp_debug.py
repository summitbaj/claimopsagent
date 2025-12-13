import sys
from app.dataverse.mcp_runner import ensure_loop, run_sync
from app.dataverse.mcp_client import get_mcp_client

if len(sys.argv) < 2:
    print("Usage: python mcp_debug.py <claim_id>")
    sys.exit(1)

claim_id = sys.argv[1]
ensure_loop()
mcp = get_mcp_client()
print('Initializing MCP...')
try:
    run_sync(mcp.initialize(), timeout=60)
    print('MCP initialized')
except Exception as e:
    print('INIT ERROR', e)
    raise

queries = [
    f"SELECT TOP 5 smvs_claimid, smvs_name, createdon FROM smvs_claim ORDER BY createdon DESC;",
    f"SELECT TOP 5 * FROM smvs_claim ORDER BY createdon DESC;",
    f"SELECT TOP 10 smvs_claimid FROM smvs_claim WHERE smvs_claimid = '{claim_id}';",
    f"SELECT TOP 10 smvs_claimid FROM smvs_claim WHERE LOWER(CAST(smvs_claimid AS NVARCHAR(100))) = LOWER('{claim_id}');",
    f"SELECT TOP 10 smvs_claimid FROM smvs_claim WHERE smvs_claimid LIKE '%{claim_id}%';",
]

for q in queries:
    print('\nQUERY:', q)
    try:
        rows = run_sync(mcp.read_query(q), timeout=30)
        print('ROWS_COUNT:', len(rows) if isinstance(rows, list) else 0)
        for i, r in enumerate(rows[:10]):
            print(i, r)
    except Exception as e:
        print('ERROR running query:', e)

# Describe the table
print('\nDESCRIBE smvs_claim:')
try:
    desc = run_sync(mcp._call_tool('describe_table', arguments={'table_name': 'smvs_claim'}, expect_list=False), timeout=30)
    print(desc)
except Exception as e:
    print('ERROR describing table:', e)
