import os
import re

def fix_imports(directory):
    # Regex to match imports that start with package names but not src.
    # We want to match "from config." but not "from src.config."
    # Also "import config" -> "import src.config"? usually "from" is used.
    
    packages = ["config", "core", "agents", "workflow", "skills", "prompts", "tools", "graph"]
    pattern = r"^(from\s+)(" + "|".join(packages) + r")(\.| )"
    regex = re.compile(pattern, re.MULTILINE)

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                new_content = regex.sub(r"\1src.\2\3", content)
                
                if new_content != content:
                    print(f"Updating imports in {path}")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)

if __name__ == "__main__":
    fix_imports("src")
