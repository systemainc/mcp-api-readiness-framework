"""Synthetic fixture: none of the agent-readiness patterns present."""


def create_item(request):
    body = request["body"]
    item = {
        "id": generate_id(),
        "name": body["name"],
    }
    save(item)
    return {"status": 201, "data": item}


def delete_item(request, item_id):
    delete(item_id)
    return {"status": 204}
