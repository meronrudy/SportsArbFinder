class Config:
    def __init__(self, region, unformatted, cutoff, api_key, interactive, save_file, offline_file, market, includeLinks=False, includeSids=False, includeBetLimits=False):
        self.region = region
        self.unformatted = unformatted
        self.cutoff = cutoff
        self.api_key = api_key
        self.interactive = interactive
        self.save_file = save_file
        self.offline_file = offline_file
        self.market = market
        self.includeLinks = includeLinks
        self.includeSids = includeSids
        self.includeBetLimits = includeBetLimits
