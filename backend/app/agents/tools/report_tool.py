from typing import Any


async def generate_report(
    *,
    title: str,
    summary: str | None = None,
    sections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Produce a deterministic Markdown report from structured data.
    """

    clean_title = title.strip()

    if not clean_title:
        raise ValueError(
            "title is required."
        )

    lines = [
        f"# {clean_title}",
    ]

    if summary:
        lines.extend(
            [
                "",
                summary.strip(),
            ]
        )

    for section in sections or []:
        heading = str(
            section.get(
                "heading",
                "Section",
            )
        ).strip()

        content = section.get(
            "content"
        )

        lines.extend(
            [
                "",
                f"## {heading}",
                "",
            ]
        )

        if isinstance(
            content,
            list,
        ):
            for item in content:
                lines.append(
                    f"- {item}"
                )

        elif isinstance(
            content,
            dict,
        ):
            for key, value in content.items():
                lines.append(
                    f"- **{key}:** {value}"
                )

        elif content is not None:
            lines.append(
                str(content)
            )

    report = "\n".join(
        lines
    ).strip()

    return {
        "title": clean_title,
        "format": "markdown",
        "report": report,
    }
