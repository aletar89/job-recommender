# job-recommender
An AI bot that compares job descriptions to your CV, rates you fit and adds a summary to an AirTable

I find this very useful as it removes the emotionaly difficult part of deciding whether to submit the application or not.

# How to use:
- Replace the CV in cv.txt with your CV and the skills evaluation in skills.txt with your skills.
- Create a .env file with your OpenAI API key and optionally AirTable key and table parameters (use the .env.example for the environ names)

## LinkedIn
- Open and run `main.py`
- If you want a different search query or number of results modify there.
You can also add arguments for location, posting age and remote.

## GlassDoor
- Visit https://www.glassdoor.com/Job/index.htm and set your search query.
- Run the `glassdoor_scraping_snippet.js` in your browser
  - Easiest way in Chrome is to open dev tools -> sources -> snippets and add it there.
  - It takes a couple of minutes to go through all the job descriptions, you can use other windows but not other tabs in the same Chrome window while it runs.
  - For progress indication there are prints to the console. To see only the prints of this script select it in the console left sidebar.
- Move the downloaded `glassdoor_exported_data.json` file to the work directory of this project.
- Running `main.py` will now parse this json and evaluate the jobs there as well.

## Other
- All the job descriptions and evaluations are cached as separate JSON files.
  - You can generate a `.csv` of the evaluations by running `ai_evaluator.py`
- If you want to add to the table jobs with a lower threshold, use the `lower_threshold.py` script, it runs over all the cached evaluations and compares the fit to the new threshold.