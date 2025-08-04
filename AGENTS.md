## Purpose
This project is a rewrite of the original single-file Flask application into a modular blueprint-based structure.  
Agents should help design and explain new features, but **must not modify or commit code themselves**.  
Instead, they guide the user through each step of implementation.

## How to Work with This Repository
1. **Review the existing docs**  
   - `docs/dev-process.md` – outlines the recommended workflow for building a feature.  
   - `docs/architecture.md` & `docs/project_structure.md` – describe how the app is organized.  
   - Other docs (`docs/api.md`, `docs/frontend.md`, etc.) should be updated whenever relevant.

2. **Provide Step‑by‑Step Guidance**  
   - For each new feature, help the user plan:
     - Required models and database changes.
     - Blueprints/routes to add.
     - Templates or frontend updates.
   - Show sample code snippets in your responses and explain what each part does.

3. **Prompt for User Actions**
   - After explaining the code, ask the user to apply the changes locally.
   - When the code looks good, prompt the user to:
     1. Update the relevant documentation.
     2. Commit the changes with a concise message.
     3. Push to GitHub.

4. **Testing**
   - Encourage running the application (`flask run`) and exercising the new routes or templates.
   - If tests are added in the future, instruct the user to run them (e.g., `pytest`).

5. **No Direct Code Changes by Agents**
   - Agents must never run git commands or modify files themselves.
   - All edits, commits, and pushes are carried out by the user.
   

Follow these guidelines to keep the codebase clean and maintainable while the project continues its modular rewrite.
