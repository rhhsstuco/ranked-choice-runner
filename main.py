from ranked_choice_application import RankedChoiceApplication


def main():
    """
    Runs the ranked choice election runner and display application.
    """

    application = RankedChoiceApplication(
        config_filepath="config.json",
    )

    application.run()


if __name__ == '__main__':
    main()
