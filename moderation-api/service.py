from repository import AdvertisementRepository, ModerationPolicyRepository
from schemas import Advertisement


class ModerationService:
    def __init__(self, repository: ModerationPolicyRepository) -> None:
        self._repository = repository

    def predict_violation(self, advertisement: Advertisement) -> bool:
        min_images = self._repository.get_min_images(advertisement.is_verified_seller)
        return advertisement.images_qty < min_images


class AdvertisementNotFoundError(Exception):
    pass


class SimplePredictionService:
    def __init__(
        self, repository: AdvertisementRepository, moderation: ModerationService,
    ) -> None:
        self._repository = repository
        self._moderation = moderation

    async def predict_violation(self, item_id: int) -> bool:
        advertisement = await self._repository.get_for_prediction(item_id)
        if advertisement is None:
            raise AdvertisementNotFoundError(item_id)
        return self._moderation.predict_violation(advertisement)
