import pytest

def test_excel_import(client, db, login_admin):
    login_admin()
    # Simulate file upload (use a small sample file in-memory)
    import io
    data = {
        'file': (io.BytesIO(b"sample excel content"), 'test.xlsx')
    }
    response = client.post('/import_excel', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert b'imported successfully' in response.data or b'Import complete' in response.data
    # Check that at least one part or record was created (assuming Part model)
    from models import Part
    assert Part.query.count() > 0
