from fastapi import FastAPI

# Create a FastAPI instance
app = FastAPI()


# Define a path operation for the root URL ("/")
@app.get("/")
async def read_root():
    """
    Returns a simple "Hello World" message.
    """
    return {"message": "Hello World"}


# Define a path operation with a path parameter
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    """
    Retrieves an item by its ID and optionally a query parameter.

    Args:
        item_id (int): The ID of the item to retrieve.
        q (str | None): An optional query string.

    Returns:
        dict: A dictionary containing the item ID and the query string (if provided).
    """
    if q:
        return {"item_id": item_id, "q": q}
    return {"item_id": item_id}
