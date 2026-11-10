from repository import ModerationPolicyRepository
from schemas import Advertisement


class ModerationService:
    def __init__(self, repository: ModerationPolicyRepository) -> None:
        self._repository = repository

    def predict_violation(self, advertisement: Advertisement) -> bool:
        min_images = self._repository.get_min_images(advertisement.is_verified_seller)
        return advertisement.images_qty < min_images
