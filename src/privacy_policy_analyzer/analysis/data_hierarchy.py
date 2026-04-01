from dataclasses import dataclass


@dataclass
class DataTypePath:
    data_type: str
    path: list[str]
    level: int
    parent_types: list[str]
    is_leaf: bool


@dataclass
class HierarchyEntry:
    types: list[str]
    children: list["HierarchyEntry"] | None

    @classmethod
    def from_dict(cls, data: dict) -> "HierarchyEntry":
        """Recursively construct HierarchyEntry from dictionary"""
        children_data = data.get("children")
        children = None

        if children_data is not None:
            children = [cls.from_dict(child) for child in children_data]

        return cls(types=data["types"], children=children)

    def find_data_type_in_hierarchy(
        self,
        data_type: str,
        current_path: list[str] = [],
        current_level: int = 0,
    ) -> DataTypePath | None:
        # Check if data_type is in current node's types
        if data_type in self.types:
            # Found it! Build the complete path
            full_path = current_path + [data_type]
            parent_types = current_path.copy()  # All types before this one

            return DataTypePath(
                data_type=data_type,
                path=full_path,
                level=current_level,
                parent_types=parent_types,
                is_leaf=self.children is None or len(self.children) == 0,
            )

        # If not found and has children, search recursively
        if self.children:
            # Add current node's primary type (first in list) to path
            new_path = current_path + [self.types[0]]

            for child in self.children:
                result = child.find_data_type_in_hierarchy(
                    data_type, new_path, current_level + 1
                )
                if result:
                    return result

        return None

    def to_dict(self) -> dict:
        """Recursively convert HierarchyEntry to dictionary"""
        return {
            "types": self.types,
            "children": [child.to_dict() for child in self.children]
            if self.children
            else None,
        }


@dataclass
class DataHierarchy:
    root: HierarchyEntry
    depth: int

    def __init__(self, root: HierarchyEntry):
        self.root = root

        # Calculate depth
        def calculate_depth(entry: HierarchyEntry) -> int:
            if not entry.children:
                return 1
            return 1 + max(calculate_depth(child) for child in entry.children)

        self.depth = calculate_depth(self.root)

    @classmethod
    def from_dict(cls, data: dict) -> "DataHierarchy":
        root_entry = HierarchyEntry.from_dict(data)
        return cls(root=root_entry)

    def find_data_type(self, data_type: str) -> DataTypePath | None:
        return self.root.find_data_type_in_hierarchy(data_type)

    def to_dict(self) -> dict:
        """Convert the entire hierarchy to a dictionary"""
        return self.root.to_dict()


DEFAULT_HIERARCHY: DataHierarchy = DataHierarchy(
    root=HierarchyEntry(
        types=["Data"],
        children=[
            HierarchyEntry(
                types=["SensitiveData", "SpecialCategoryData"],
                children=[
                    HierarchyEntry(
                        types=["HealthData"],
                        children=[
                            HierarchyEntry(types=["HealthStatus"], children=None),
                            HierarchyEntry(types=["SleepData"], children=None),
                            HierarchyEntry(types=["CoughingData"], children=None),
                            HierarchyEntry(types=["SnoringData"], children=None),
                            HierarchyEntry(types=["HeartRateData"], children=None),
                            HierarchyEntry(types=["StepCountData"], children=None),
                            HierarchyEntry(types=["FitnessGoals"], children=None),
                            HierarchyEntry(
                                types=["FitnessChallengeResults"], children=None
                            ),
                            HierarchyEntry(types=["HeartRate"], children=None),
                            HierarchyEntry(types=["BloodPressure"], children=None),
                            HierarchyEntry(types=["BloodSugar"], children=None),
                            HierarchyEntry(types=["BloodOxygenLevel"], children=None),
                            HierarchyEntry(types=["BMI"], children=None),
                            HierarchyEntry(types=["BodyFat"], children=None),
                            HierarchyEntry(types=["MuscleMass"], children=None),
                            HierarchyEntry(
                                types=["MetabolicInformation"], children=None
                            ),
                            HierarchyEntry(types=["MenstrualCycleData"], children=None),
                            HierarchyEntry(types=["BoneDensity"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["PhysicalBodyMetrics"],
                        children=[
                            HierarchyEntry(types=["Height"], children=None),
                            HierarchyEntry(types=["Weight"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["FinancialData"],
                        children=[
                            HierarchyEntry(
                                types=["PaymentData"],
                                children=[
                                    HierarchyEntry(
                                        types=["PaymentAmount"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["PaymentMethod"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["BillingData"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["BillingReceipts"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["TransactionData"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["InAppTransactions"],
                                        children=None,
                                    ),
                                    HierarchyEntry(
                                        types=["InvoiceData"], children=None
                                    ),
                                ],
                            ),
                            HierarchyEntry(
                                types=["BankAccountInformation"],
                                children=[
                                    HierarchyEntry(
                                        types=["BankAccountNumber"],
                                        children=None,
                                    ),
                                    HierarchyEntry(
                                        types=["BankHolderName"], children=None
                                    ),
                                ],
                            ),
                            HierarchyEntry(
                                types=["CreditCardInformation"],
                                children=[
                                    HierarchyEntry(
                                        types=["CreditCardNumber"],
                                        children=None,
                                    ),
                                    HierarchyEntry(
                                        types=["CardExpiryDate"], children=None
                                    ),
                                ],
                            ),
                            HierarchyEntry(
                                types=["DebitCardInformation"], children=None
                            ),
                            HierarchyEntry(
                                types=["PaymentCardInformation"],
                                children=[
                                    HierarchyEntry(
                                        types=["PaymentCardNumber"], children=None
                                    ),
                                ],
                            ),
                            HierarchyEntry(types=["IncomeData"], children=None),
                            HierarchyEntry(
                                types=["FinancialStatus"],
                                children=[
                                    HierarchyEntry(
                                        types=["CreditScore"], children=None
                                    ),
                                ],
                            ),
                        ],
                    ),
                    HierarchyEntry(
                        types=["SexualLife"],
                        children=[
                            HierarchyEntry(types=["SexualOrientation"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["BiometricData"],
                        children=[
                            HierarchyEntry(types=["FacialData"], children=None),
                            HierarchyEntry(types=["FingerprintData"], children=None),
                            HierarchyEntry(
                                types=["VoiceData", "VoiceCharacteristics"],
                                children=None,
                            ),
                        ],
                    ),
                    HierarchyEntry(
                        types=["CredentialData", "SecurityInformation"],
                        children=[
                            HierarchyEntry(types=["Password"], children=None),
                            HierarchyEntry(types=["SecurityPin"], children=None),
                            HierarchyEntry(types=["AuthToken"], children=None),
                        ],
                    ),
                    HierarchyEntry(types=["EmergencyData"], children=None),
                    HierarchyEntry(types=["PoliticalAffiliations"], children=None),
                    HierarchyEntry(types=["ReligiousBeliefs"], children=None),
                    HierarchyEntry(types=["TradeUnionMembership"], children=None),
                    HierarchyEntry(types=["CriminalOffenses"], children=None),
                    HierarchyEntry(types=["SocialAssistanceData"], children=None),
                ],
            ),
            HierarchyEntry(
                types=["PersonalData", "PII"],
                children=[
                    HierarchyEntry(
                        types=["Identifier", "IdentityInformation"],
                        children=[
                            HierarchyEntry(types=["DeviceID"], children=None),
                            HierarchyEntry(types=["SerialNumber"], children=None),
                            HierarchyEntry(types=["AccountID"], children=None),
                            HierarchyEntry(types=["AdvertisingID"], children=None),
                            HierarchyEntry(types=["SessionID"], children=None),
                            HierarchyEntry(types=["UserID"], children=None),
                            HierarchyEntry(types=["OpenID"], children=None),
                            HierarchyEntry(types=["GoogleAdID"], children=None),
                            HierarchyEntry(types=["WindowsAdID"], children=None),
                            HierarchyEntry(types=["AndroidID"], children=None),
                            HierarchyEntry(types=["SpaceID"], children=None),
                            HierarchyEntry(types=["ClickID"], children=None),
                            HierarchyEntry(types=["FCMToken"], children=None),
                            HierarchyEntry(types=["MACAddress"], children=None),
                            HierarchyEntry(types=["IPAddress"], children=None),
                            HierarchyEntry(
                                types=["SIMInformation"],
                                children=[
                                    HierarchyEntry(types=["ICCID"], children=None),
                                    HierarchyEntry(types=["IMSI"], children=None),
                                    HierarchyEntry(types=["IMEI"], children=None),
                                ],
                            ),
                            HierarchyEntry(
                                types=["GovernmentID"],
                                children=[
                                    HierarchyEntry(
                                        types=["SocialSecurityNumber"], children=None
                                    ),
                                    HierarchyEntry(types=["Passport"], children=None),
                                    HierarchyEntry(
                                        types=["DriverLicense"], children=None
                                    ),
                                    HierarchyEntry(types=["TaxID"], children=None),
                                ],
                            ),
                        ],
                    ),
                    HierarchyEntry(
                        types=["Name"],
                        children=[
                            HierarchyEntry(types=["FirstName"], children=None),
                            HierarchyEntry(types=["LastName"], children=None),
                            HierarchyEntry(types=["Nickname"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["ContactInformation"],
                        children=[
                            HierarchyEntry(types=["EmailAddress"], children=None),
                            HierarchyEntry(types=["PhoneNumber"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["LocationData"],
                        children=[
                            HierarchyEntry(types=["LocationHistory"], children=None),
                            HierarchyEntry(types=["GPSData"], children=None),
                            HierarchyEntry(types=["Coordinates"], children=None),
                            HierarchyEntry(types=["AltitudeData"], children=None),
                            HierarchyEntry(types=["Timezone"], children=None),
                            HierarchyEntry(types=["Address"], children=None),
                            HierarchyEntry(types=["AreaCode"], children=None),
                            HierarchyEntry(types=["City"], children=None),
                            HierarchyEntry(types=["Country"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["DemographicData"],
                        children=[
                            HierarchyEntry(types=["Age"], children=None),
                            HierarchyEntry(types=["Gender"], children=None),
                            HierarchyEntry(types=["DateOfBirth"], children=None),
                            HierarchyEntry(types=["Nationality"], children=None),
                            HierarchyEntry(types=["Ethnicity"], children=None),
                            HierarchyEntry(types=["Language"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["BiographicInformation"],
                        children=[
                            HierarchyEntry(
                                types=["EducationalBackground"],
                                children=[
                                    HierarchyEntry(
                                        types=["Qualifications"], children=None
                                    ),
                                ],
                            ),
                            HierarchyEntry(
                                types=["EmploymentBackground"],
                                children=[
                                    HierarchyEntry(types=["Employer"], children=None),
                                ],
                            ),
                            HierarchyEntry(types=["CurriculumVitae"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["AccountData"],
                        children=[
                            HierarchyEntry(types=["ProfileData"], children=None),
                            HierarchyEntry(types=["Username"], children=None),
                            HierarchyEntry(types=["ProfilePicture"], children=None),
                            HierarchyEntry(types=["ThirdPartyHandle"], children=None),
                            HierarchyEntry(types=["RegistrationData"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["PersonalBehaviorData"],
                        children=[
                            HierarchyEntry(types=["HabitData"], children=None),
                            HierarchyEntry(types=["InterestData"], children=None),
                            HierarchyEntry(types=["HobbyData"], children=None),
                            HierarchyEntry(types=["PurchaseMotivation"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["LifestyleInformation"],
                        children=[
                            HierarchyEntry(types=["NumberOfChildren"], children=None),
                            HierarchyEntry(
                                types=["PetInformation"],
                                children=[
                                    HierarchyEntry(
                                        types=["NumberOfPets"], children=None
                                    ),
                                ],
                            ),
                        ],
                    ),
                    HierarchyEntry(types=["FamilyInformation"], children=None),
                    HierarchyEntry(types=["FriendsInformation"], children=None),
                    HierarchyEntry(
                        types=["PermissionsData"],
                        children=[
                            HierarchyEntry(types=["CameraPermissions"], children=None),
                            HierarchyEntry(
                                types=["MicrophonePermissions"], children=None
                            ),
                            HierarchyEntry(
                                types=["LocationPermissions"], children=None
                            ),
                            HierarchyEntry(
                                types=["ContactsPermissions"], children=None
                            ),
                            HierarchyEntry(types=["StoragePermissions"], children=None),
                            HierarchyEntry(
                                types=["NotificationPermissions"], children=None
                            ),
                        ],
                    ),
                    HierarchyEntry(types=["WrittenPermissions"], children=None),
                    HierarchyEntry(types=["UserPreferences"], children=None),
                    HierarchyEntry(types=["Contacts"], children=None),
                    HierarchyEntry(
                        types=["CommunicationRecords"],
                        children=[
                            HierarchyEntry(types=["CallRecords"], children=None),
                            HierarchyEntry(types=["ChatHistory"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["CandidateInformation"],
                        children=None,
                    ),
                ],
            ),
            HierarchyEntry(
                types=["NPII", "GeneralInformation"],
                children=[
                    HierarchyEntry(
                        types=["DeviceInformation"],
                        children=[
                            HierarchyEntry(
                                types=["TechnicalInformation"],
                                children=[
                                    HierarchyEntry(
                                        types=["ManufacturerInformation"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["FirmwareVersion"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["HardwareInformation"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["HardwareVersion"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["OperatingSystem"], children=None
                                    ),
                                ],
                            ),
                            HierarchyEntry(types=["DeviceName"], children=None),
                            HierarchyEntry(types=["DeviceType"], children=None),
                            HierarchyEntry(types=["DeviceState"], children=None),
                            HierarchyEntry(
                                types=["BrowserInformation"],
                                children=[
                                    HierarchyEntry(
                                        types=["BrowserType"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["BrowserVersion"], children=None
                                    ),
                                ],
                            ),
                            HierarchyEntry(types=["ScreenResolution"], children=None),
                            HierarchyEntry(types=["BatteryData"], children=None),
                            HierarchyEntry(types=["MemoryUsage"], children=None),
                            HierarchyEntry(types=["StorageUsage"], children=None),
                            HierarchyEntry(types=["CpuUsage"], children=None),
                            HierarchyEntry(types=["DeviceTemperature"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["AppInformation"],
                        children=[
                            HierarchyEntry(types=["AppVersion"], children=None),
                            HierarchyEntry(types=["AppName"], children=None),
                            HierarchyEntry(types=["PartnerApp"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["WebsiteInformation"],
                        children=[
                            HierarchyEntry(types=["Referrer"], children=None),
                            HierarchyEntry(types=["HostName"], children=None),
                            HierarchyEntry(types=["URL"], children=None),
                            HierarchyEntry(types=["Clickstream"], children=None),
                            HierarchyEntry(types=["PageResponseTime"], children=None),
                            HierarchyEntry(types=["Clicks"], children=None),
                            HierarchyEntry(types=["ScrollData"], children=None),
                            HierarchyEntry(types=["MouseMovements"], children=None),
                            HierarchyEntry(types=["Keystrokes"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["UsageData"],
                        children=[
                            HierarchyEntry(types=["UsageDuration"], children=None),
                            HierarchyEntry(types=["UsageFrequency"], children=None),
                            HierarchyEntry(
                                types=["BrowsingActivity"],
                                children=[
                                    HierarchyEntry(
                                        types=["VisitedPages"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["ViewedContent"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["ClickedLinks"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["SearchHistory"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["PageInteractions"], children=None
                                    ),
                                ],
                            ),
                            HierarchyEntry(types=["DeviceInteractions"], children=None),
                            HierarchyEntry(
                                types=["AppInteraction"],
                                children=[
                                    HierarchyEntry(
                                        types=["ScreenUnlocks"], children=None
                                    ),
                                    HierarchyEntry(types=["TouchData"], children=None),
                                ],
                            ),
                            HierarchyEntry(types=["ContentUseHistory"], children=None),
                            HierarchyEntry(types=["EngagementMetrics"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["SetupInformation"],
                        children=[
                            HierarchyEntry(types=["ActivationTime"], children=None),
                            HierarchyEntry(
                                types=["SettingsData"],
                                children=[
                                    HierarchyEntry(types=["FontSize"], children=None),
                                    HierarchyEntry(
                                        types=["ConfigurationData"], children=None
                                    ),
                                ],
                            ),
                        ],
                    ),
                    HierarchyEntry(
                        types=["LogData"],
                        children=[
                            HierarchyEntry(types=["LogFiles"], children=None),
                            HierarchyEntry(types=["AccessLogs"], children=None),
                            HierarchyEntry(types=["DeviceLogs"], children=None),
                            HierarchyEntry(types=["Errors"], children=None),
                            HierarchyEntry(types=["ActivityLogs"], children=None),
                            HierarchyEntry(types=["MaintenanceLogs"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["NetworkData"],
                        children=[
                            HierarchyEntry(
                                types=["CustomerProprietaryNetworkInformation"],
                                children=None,
                            ),
                            HierarchyEntry(
                                types=["OtherElectronicNetworkActivityInformation"],
                                children=None,
                            ),
                            HierarchyEntry(
                                types=["MobileNetworkData"],
                                children=[
                                    HierarchyEntry(
                                        types=["MobileNetworkCode"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["MobileCountryCode"], children=None
                                    ),
                                ],
                            ),
                            HierarchyEntry(types=["ConnectionData"], children=None),
                            HierarchyEntry(types=["DataAmount"], children=None),
                            HierarchyEntry(types=["InternetSpeed"], children=None),
                            HierarchyEntry(
                                types=["InternetServiceProvider"], children=None
                            ),
                            HierarchyEntry(
                                types=["WiFiData"],
                                children=[
                                    HierarchyEntry(types=["WiFiStatus"], children=None),
                                    HierarchyEntry(
                                        types=["WiFiHeatmap"], children=None
                                    ),
                                    HierarchyEntry(types=["SSID"], children=None),
                                ],
                            ),
                            HierarchyEntry(types=["SignalStrength"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["TelemetryData"],
                        children=[
                            HierarchyEntry(types=["DeviceStatistics"], children=None),
                            HierarchyEntry(types=["PerformanceData"], children=None),
                            HierarchyEntry(types=["DiagnosticData"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["StatisticalData"],
                        children=None,
                    ),
                    HierarchyEntry(
                        types=["SensorData"],
                        children=[
                            HierarchyEntry(
                                types=["EnvironmentalData"],
                                children=[
                                    HierarchyEntry(
                                        types=["TemperatureData"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["HumidityData"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["MoistureData"], children=None
                                    ),
                                    HierarchyEntry(types=["NoiseLevel"], children=None),
                                    HierarchyEntry(
                                        types=["PrecipitationData"], children=None
                                    ),
                                    HierarchyEntry(types=["WindData"], children=None),
                                    HierarchyEntry(
                                        types=["AirQualityData"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["CarbonMonoxideData"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["CarbonDioxideData"], children=None
                                    ),
                                    HierarchyEntry(types=["SmokeData"], children=None),
                                    HierarchyEntry(
                                        types=["OutdoorData"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["WeatherData"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["AmbientLightData"], children=None
                                    ),
                                    HierarchyEntry(types=["Lighting"], children=None),
                                ],
                            ),
                            HierarchyEntry(types=["MotionData"], children=None),
                            HierarchyEntry(
                                types=["PresenceData"],
                                children=[
                                    HierarchyEntry(
                                        types=["PresenceOfPeople"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["PresenceOfPets"], children=None
                                    ),
                                ],
                            ),
                            HierarchyEntry(
                                types=["WaterConsumptionData"], children=None
                            ),
                            HierarchyEntry(types=["GasConsumptionData"], children=None),
                            HierarchyEntry(types=["DirtLevel"], children=None),
                            HierarchyEntry(
                                types=["FloorplanData"],
                                children=[
                                    HierarchyEntry(types=["HomeName"], children=None),
                                    HierarchyEntry(types=["FloorType"], children=None),
                                    HierarchyEntry(types=["ObjectData"], children=None),
                                    HierarchyEntry(types=["RoomName"], children=None),
                                ],
                            ),
                            HierarchyEntry(types=["OperatingPowerData"], children=None),
                            HierarchyEntry(
                                types=["EnergyConsumptionData"], children=None
                            ),
                            HierarchyEntry(types=["VoltageData"], children=None),
                            HierarchyEntry(
                                types=["EnergyProductivityData"], children=None
                            ),
                        ],
                    ),
                    HierarchyEntry(
                        types=["ScheduleTimes"],
                        children=[
                            HierarchyEntry(types=["CleaningHistory"], children=None),
                            HierarchyEntry(types=["HeatingSchedule"], children=None),
                            HierarchyEntry(types=["WateringSchedule"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["MediaData"],
                        children=[
                            HierarchyEntry(
                                types=["AudioData"],
                                children=[
                                    HierarchyEntry(
                                        types=["VoiceCommands"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["AmbientSound"], children=None
                                    ),
                                    HierarchyEntry(types=["Music"], children=None),
                                ],
                            ),
                            HierarchyEntry(types=["VideoData"], children=None),
                            HierarchyEntry(
                                types=["ImageData"],
                                children=[
                                    HierarchyEntry(
                                        types=["Screenshots"], children=None
                                    ),
                                    HierarchyEntry(types=["Drawings"], children=None),
                                ],
                            ),
                            HierarchyEntry(types=["TextData"], children=None),
                            HierarchyEntry(types=["OtherFileData"], children=None),
                            HierarchyEntry(types=["DesignFiles"], children=None),
                            HierarchyEntry(types=["Maps"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["UserGeneratedContent", "Submissions"],
                        children=[
                            HierarchyEntry(types=["Feedback"], children=None),
                            HierarchyEntry(types=["Comments"], children=None),
                            HierarchyEntry(types=["Opinions"], children=None),
                            HierarchyEntry(types=["Reviews"], children=None),
                            HierarchyEntry(types=["Likes"], children=None),
                            HierarchyEntry(types=["Follows"], children=None),
                            HierarchyEntry(types=["Ratings"], children=None),
                            HierarchyEntry(types=["Testimonial"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["CommercialInformation"],
                        children=[
                            HierarchyEntry(
                                types=["OrderData"],
                                children=[
                                    HierarchyEntry(
                                        types=["OrderHistory"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["OrderNumber"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["PurchaseDate"], children=None
                                    ),
                                    HierarchyEntry(
                                        types=["ShippingInformation"], children=None
                                    ),
                                ],
                            ),
                            HierarchyEntry(types=["CustomerList"], children=None),
                            HierarchyEntry(types=["CustomerRecords"], children=None),
                            HierarchyEntry(types=["MembershipData"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["ServicesData"],
                        children=[
                            HierarchyEntry(types=["ServiceType"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["ApplicationData"],
                        children=None,
                    ),
                    HierarchyEntry(
                        types=["SecurityInformationNPII"],
                        children=[
                            HierarchyEntry(types=["TamperStatus"], children=None),
                            HierarchyEntry(types=["VirusDefinitions"], children=None),
                        ],
                    ),
                    HierarchyEntry(
                        types=["BusinessInformation"],
                        children=[
                            HierarchyEntry(types=["NumberOfEmployees"], children=None),
                            HierarchyEntry(types=["BusinessModel"], children=None),
                        ],
                    ),
                    HierarchyEntry(types=["DateTime"], children=None),
                    HierarchyEntry(
                        types=["Events"],
                        children=[
                            HierarchyEntry(types=["DeviceEvents"], children=None),
                            HierarchyEntry(types=["DrivingEvents"], children=None),
                        ],
                    ),
                    HierarchyEntry(types=["ContestData"], children=None),
                    HierarchyEntry(
                        types=["Status"],
                        children=[
                            HierarchyEntry(types=["OnlineStatus"], children=None),
                            HierarchyEntry(types=["CallStatus"], children=None),
                        ],
                    ),
                ],
            ),
        ],
    )
)
