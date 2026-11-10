class ModerationPolicyRepository:
    _MIN_IMAGES = {True: 0, False: 1}

    def get_min_images(self, is_verified_seller: bool) -> int:
        return self._MIN_IMAGES[is_verified_seller]
