from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os
from main import convert_pdf_and_upload_to_notion


app = FastAPI()
from config import (
    NOTION_TOKEN,
    NOTION_PAGE_ID,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import aspose.slides as slides


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Create upload directory if it doesn't exist
    UPLOAD_DIRECTORY = "/tmp/uploads"
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

    try:
        # Save the uploaded file
        file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_location, "wb+") as buffer:
            contents = await file.read()
            buffer.write(contents)

        # Convert PPT to PDF if necessary
        if file.filename.endswith((".ppt", ".pptx")):
            pdf_location = os.path.join(
                UPLOAD_DIRECTORY, file.filename.rsplit(".", 1)[0] + ".pdf"
            )
            presentation = slides.Presentation(file_location)
            presentation.save(pdf_location, slides.export.SaveFormat.PDF)
            file_to_process = pdf_location
        else:
            file_to_process = file_location

        # Process the file using your existing conversion logic
        result = convert_pdf_and_upload_to_notion(
            pdf_path=file_to_process,
            notion_page_id=NOTION_PAGE_ID,
            notion_token=NOTION_TOKEN,
            imgur_client_id=None,  # Remove if not needed
        )

        return {"success": True, "filename": file.filename}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        # Clean up temporary files
        if os.path.exists(file_location):
            os.remove(file_location)
        if "pdf_location" in locals() and os.path.exists(pdf_location):
            os.remove(pdf_location)


# Add health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
