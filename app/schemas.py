from pydantic import BaseModel, model_validator, ValidationError, ConfigDict

class ProductFilterSchema(BaseModel):
    # 🎯 Define Allowed Fields
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
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def check_exclusive_fields(self):

        age_fields = [
            self.age_0_2, self.age_3_5, self.age_6_12, self.age_13_18,
            self.age_19_29, self.age_30_45, self.age_45_65, self.age_65_plus
        ]
        if sum(age_fields) > 1:
            raise ValueError("Only one age group can be selected.")


        gender_fields = [self.gender_male, self.gender_female]
        if sum(gender_fields) > 1:
            raise ValueError("Only one gender can be selected.")


        special_fields = [
            self.special_birthday, self.special_anniversary, self.special_valentines,
            self.special_new_year, self.special_house_warming, self.special_mothers_day,
            self.special_fathers_day
        ]
        if sum(special_fields) > 1:
            raise ValueError("Only one special day can be selected.")

        return self
