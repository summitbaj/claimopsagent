from app.core.config import settings

def main():
    print('MCP_CONNECTION_URL=', settings.MCP_CONNECTION_URL)
    print('DATAVERSE_URL=', settings.DATAVERSE_URL)

if __name__ == '__main__':
    main()
