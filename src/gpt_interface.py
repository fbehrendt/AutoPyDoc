def send_batch(batch, callback):
    mocked_result = {
        "id": batch["id"],
        # TODO
    }
    callback(mocked_result)