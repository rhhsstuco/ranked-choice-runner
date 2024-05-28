from ranked_choice_application import RankedChoiceApplication


def main():
    application = RankedChoiceApplication(
        metadata="metadata.csv",
        candidates_running=4,
        candidates_required=2,
        ballot_size=4,
        threshold=0.5,
        display_delay=0.75
    )

    application.run()


if __name__ == '__main__':
    main()
