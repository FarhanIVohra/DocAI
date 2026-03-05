print("Testing imports...")
try:
    from services.repo_indexer import RepoIndexer
    print("RepoIndexer imported")
    from services.doc_generator import DocGenerator
    print("DocGenerator imported")
    from services.chat_agent import ChatAgent
    print("ChatAgent imported")
except Exception as e:
    import traceback
    traceback.print_exc()
print("Test complete")
