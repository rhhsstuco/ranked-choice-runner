from ranked_choice_application import RankedChoiceApplication


def main():
    application = RankedChoiceApplication(
        metadata={
            "MUN Elections": "data.csv"
        },
        candidates_running=4,
        candidates_required=2,
        ballot_size=4,
        threshold=0.5,
    )

    application.run()


if __name__ == '__main__':
    main()
