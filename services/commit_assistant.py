"""
commit_assistant.py
───────────────────
Elite Utility: Automatically generates a professional Git commit 
message based on staged changes (git diff).
"""

import subprocess
import os
from services.llm_service import get_llm

def get_staged_diff():
    try:
        return subprocess.check_output(["git", "diff", "--cached"], stderr=subprocess.STDOUT).decode("utf-8")
    except Exception as e:
        print(f"❌ Git error: {e}")
        return None

def main():
    print("🤖 AutoDoc AI Commit Assistant")
    print("------------------------------")
    
    diff = get_staged_diff()
    
    if not diff:
        print("💡 No staged changes found. Use 'git add <file>' first.")
        return

    # Truncate if too large for LLM context
    if len(diff) > 8000:
        diff = diff[:8000] + "\n\n...(diff truncated)..."

    llm = get_llm()
    system = "You are a Git Commit Expert. Write a professional, concise Conventional Commit message based on the provided diff. Only return the commit message text. Use emoji if appropriate."
    user = f"Write a commit message for these changes:\n\n{diff}"

    print("🧠 Analyzing code changes...")
    msg = llm.generate(user, system, max_tokens=100)
    
    print("\n📝 Proposed Commit Message:")
    print("-" * 30)
    print(msg.strip())
    print("-" * 30)
    print("\nTo use: git commit -m \"" + msg.strip().replace('"', '\\"') + "\"")

if __name__ == "__main__":
    main()
