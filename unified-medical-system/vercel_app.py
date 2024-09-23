from app import create_app

app = create_app()

# This is for Vercel serverless function
def handler(request, response):
    return app(request, response)