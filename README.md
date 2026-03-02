AI Chatbot utilizing GraphRAG to serve as an assistant to Purdue academic advisors.

## Running Locally

Make sure the React website is up to date:

```bash
cd website
npm run build
```

then run on localhost, making sure you pass in an API key and have everything in requirements.txt.

```bash
cd ../server
export OPENAI_API_KEY="PUT YOUR API KEY HERE"
python3 run.py
```

## Future Plans

- *Set up sql database*: All documents in user_uploads should be tracked by their time of upload, filename, the user who uploaded the infromation, number of succesful RAG queries (thumbs up) and unsuccessful. (This allows us to prune out database at a later time).

- *Add a student chat room*: Students can ask questions and get their questions answered. These questions and their answers will be stored in a database as well, sorted by class. The chat room will be divided by class and topics, and students can choose where to post their information. The database will use one of its columns to track this. If a student has a similar question to the user, there can be an option to subsitute that question for the current student's question. A question can also reference documents if it has a successful answer (user liked the question).

- Train local LLM model

- Organize the graph tool

- Organize website

- Crawl course catalogue for all engineering and CS and DS courses. Ideally also crawl all prereq sheets for each class in all three majors.

- Get a TON more emails to use on API keys.

- Finish cleaner.py module

