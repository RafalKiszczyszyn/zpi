ENV = "production"

settings = None
if ENV == "dev":
    import feedreader.env.dev.settings as dev
    settings = dev
elif ENV == "production":
    import feedreader.env.production.settings as production
    settings = production
elif ENV == "test":
    import feedreader.env.test.settings as test
    settings = test