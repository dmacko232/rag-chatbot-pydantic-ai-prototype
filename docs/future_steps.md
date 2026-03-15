# Future steps

- get proper CI/CD :) 
- move to real SQL db (postgre), not sqlite
- move to proper vector DB -- would need analysis which one (and what is whitelisted lol)
- RAG itself could be further imrpoved with proper eval in place, for example change chunking, try out diff models, add more dive
- the chatbot app could be improved -- allow users to specify custom prompts, allow users to send feedback, ..
- possibly add things like caching with Redis
- deploy the app in platform on cloud
- add actual offline evals etc using Arize Phoenix. Improve the evals, do not eval just Q&A pairs but evaluate also scenarios
- online evaluation could be added
- deal with many operations for production (how to easily do experiments when we wanna change data pipeline, how to keep data in sync)
- change indexing algo for vector store with more docs (use HNSW)