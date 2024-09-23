from run import app

# This is for Vercel serverless function
def handler(request, response):
    return app(request, response)