I used claude code the whole time for both coding/ fast debugging. When given the spec I wrote out all my ideas and my plan with pen and paper. After that I had claude implement it and use my other research repo as reference for the ai (langchain/chroma) code.

I was really involved the whole process as I had to debug/change directions a ton.

Claude failed a lot in regards to my retrieval agent and I had to make it move away from a ReAct agent into a regular one with tools because it was blowing up the codebase with bloat and bad imports. I chose a simpler version for simplicity here.

I listed all my design decisions in the readme and can explain how I interacted with claude for every file/commit in the interview. Enumerating those interactions here would be unoptimal given how much I went back and forth with claude over things.