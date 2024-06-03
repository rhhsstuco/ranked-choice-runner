from ranked_choice_application import RankedChoiceApplication


def main():
    application = RankedChoiceApplication(
        metadata_filepath="config.json",
    )

    application.run()


if __name__ == '__main__':
    main()
