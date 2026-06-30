from fastapi import Header, HTTPException

def verify_admin_token(x_admin_token: str | None = Header(None)):
    """
    Dummy authenticator for now.
    In the future, this will validate a real JWT or API key
    to protect the /admin/ routes from unauthorized access.
    """
    # For now, we allow access without token during development.
    # To enable protection, uncomment the lines below:
    # if not x_admin_token or x_admin_token != "EXPECTED_TOKEN":
    #     raise HTTPException(status_code=401, detail="Unauthorized")
    return True
