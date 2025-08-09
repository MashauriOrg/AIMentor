import express from "express";
import multer from "multer";
import OpenAI from "openai";

const app = express();
const upload = multer();
const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

app.post("/chat", upload.single("file"), async (req, res) => {
  const text = req.body.text;
  const fileBuffer = req.file?.buffer;

  let fileId;
  if (fileBuffer) {
    const up = await client.files.create({
      file: fileBuffer,
      purpose: "assistants"
    });
    fileId = up.id;
  }

  const response = await client.chat.completions.create({
    model: "gpt-4.1",
    messages: [{ role: "user", content: text }],
    ...(fileId && { files: [fileId] })
  });

  res.json({ reply: response.choices[0].message.content });
});

app.listen(3000);
