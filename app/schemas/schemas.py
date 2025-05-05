from pydantic import BaseModel, model_validator, ConfigDict, Field
from typing import List,Optional

class LoginCredentials(BaseModel):
    email: str
    password: str

class FeatureInput(BaseModel):
    gender: Optional[str]
    age: Optional[str]
    special: Optional[str]
    interests: List[str] = []
    min_budget: Optional[float] = Field(default=None, ge=0)
    max_budget: Optional[float] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def check_required_fields(self) -> "FeatureInput":
        if not self.gender or not self.age or not self.special:
            raise ValueError("Cinsiyet, yaş ve özel gün alanları zorunludur.")
        return self

class ProductRecommendation(BaseModel):
    algorithm: str
    product_id: int
    recommended_order: int
    is_selected: bool
    bad_recommendation: bool = False

class BlindTestSubmission(BaseModel):
    email: str
    session_parameters: FeatureInput
    selections: List[ProductRecommendation]

class ProductFilterSchema(BaseModel):
    age_0_2: bool = False
    age_3_5: bool = False
    age_6_12: bool = False
    age_13_18: bool = False
    age_19_29: bool = False
    age_30_45: bool = False
    age_45_65: bool = False
    age_65_plus: bool = False

    gender_male: bool = False
    gender_female: bool = False

    special_birthday: bool = False
    special_anniversary: bool = False
    special_valentines: bool = False
    special_new_year: bool = False
    special_house_warming: bool = False
    special_mothers_day: bool = False
    special_fathers_day: bool = False

    interest_sports: bool = False
    interest_music: bool = False
    interest_books: bool = False
    interest_technology: bool = False
    interest_travel: bool = False
    interest_art: bool = False
    interest_food: bool = False
    interest_fitness: bool = False
    interest_health: bool = False
    interest_photography: bool = False
    interest_fashion: bool = False
    interest_pets: bool = False
    interest_home_decor: bool = False
    interest_movies_tv: bool = False

    min_budget: Optional[float] = Field(default=None, ge=0)
    max_budget: Optional[float] = Field(default=None, ge=0)

    model_config = ConfigDict(extra="forbid")

    @property
    def has_age(self):
        return any([
            self.age_0_2, self.age_3_5, self.age_6_12, self.age_13_18,
            self.age_19_29, self.age_30_45, self.age_45_65, self.age_65_plus
        ])

    @property
    def has_gender(self):
        return self.gender_male or self.gender_female

    @property
    def has_special(self):
        return any([
            self.special_birthday, self.special_anniversary, self.special_valentines,
            self.special_new_year, self.special_house_warming, self.special_mothers_day,
            self.special_fathers_day
        ])

    @property
    def has_interests(self):
        return any([
            self.interest_sports, self.interest_music, self.interest_books,
            self.interest_technology, self.interest_travel, self.interest_art,
            self.interest_food, self.interest_fitness, self.interest_health,
            self.interest_photography, self.interest_fashion, self.interest_pets,
            self.interest_home_decor, self.interest_movies_tv
        ])

    def get_missing_fields(self) -> List[str]:
        missing = []
        if not self.has_age:
            missing.append("Yaş aralığını belirtir misiniz?")
        if not self.has_gender:
            missing.append("Hediye alacağınız kişinin cinsiyeti nedir?")
        if not self.has_special:
            missing.append("Bu hediye özel bir gün için mi? (Doğum günü, yıl dönümü vb.)")
        if not self.has_interests:
            missing.append("Kişinin ilgi alanlarından birkaçını paylaşır mısınız? (Örneğin, spor, müzik, teknoloji vb.)")
        if self.min_budget is not None and self.max_budget is not None:
            if self.min_budget > self.max_budget:
                raise ValueError("Minimum bütçe, maksimum bütçeden büyük olamaz.")
        return missing

    @model_validator(mode="after")
    def check_exclusive_fields(self):
        if sum([
            self.age_0_2, self.age_3_5, self.age_6_12, self.age_13_18,
            self.age_19_29, self.age_30_45, self.age_45_65, self.age_65_plus
        ]) > 1:
            raise ValueError("Only one age group can be selected.")

        if self.gender_male and self.gender_female:
            raise ValueError("Only one gender can be selected.")

        if sum([
            self.special_birthday, self.special_anniversary, self.special_valentines,
            self.special_new_year, self.special_house_warming, self.special_mothers_day,
            self.special_fathers_day
        ]) > 1:
            raise ValueError("Only one special day can be selected.")

        return self
