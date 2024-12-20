import { exec } from 'child_process';
import { NextResponse } from 'next/server';
import path from 'path';
import fs, { writeFile } from 'fs';


export async function POST(req: Request) {
  try {
    
    const formData = await req.formData();
    const file = formData.get('file') as File;
    if (!file) {
      return NextResponse.json(
          { error: 'No file uploaded' },
          { status: 400 }
      );
  }
  
  try {
      // Save file temporarily
      const tempDir = path.join(process.cwd(), 'temp');
      if (!fs.existsSync(tempDir)) {
          fs.mkdirSync(tempDir, { recursive: true });
      }
  
      const tempPath = path.join(tempDir, file.name);
      const fileBuffer = Buffer.from(await file.arrayBuffer());
      
      await new Promise<void>((resolve, reject) => {
          writeFile(tempPath, fileBuffer, (err) => {
              if (err) reject(err);
              else resolve();
          });
      });
      
    // Execute Python script
    return new Promise((resolve) => {
      
      
      exec(`source virenv/bin/activate && python3 convert_slides.py "${tempPath}"`, (error, stdout) => {
        // Clean up temp file
        
        fs.unlinkSync(tempPath);

        if (error) {
          console.log("hello");
          console.log(tempPath);
          resolve(NextResponse.json({ error: error.message }, { status: 500 }));
          return;
        }
        console.log("hello");
        try {
          const result = JSON.parse(stdout);
          resolve(NextResponse.json(result));
        } catch {
          resolve(NextResponse.json({ error: 'Invalid response from script' }, { status: 500 }));
        }
      });
    });
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json({ error: 'Failed to process file' }, { status: 500 });
  }
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json({ error: 'Failed to upload file' }, { status: 500 });
  }
}