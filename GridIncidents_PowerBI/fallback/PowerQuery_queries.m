// ===== GetCsv (function; needs parameter DataBaseUrl) =====
(fileName as text) as table =>
let
    // DataBaseUrl is a parameter: an https:// folder URL (default: the GitHub repo)
    // or a local folder path such as C:\Data\processed
    Source =
        if Text.StartsWith(DataBaseUrl, "http") then
            Csv.Document(
                Web.Contents(DataBaseUrl, [RelativePath = fileName]),
                [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
            )
        else
            Csv.Document(
                File.Contents(DataBaseUrl & "\" & fileName),
                [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
            ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true])
in
    Promoted

// ===== fact_events =====
let
    Source = GetCsv("fact_events.csv"),
    Typed = Table.TransformColumnTypes(
        Source,
        {
            {"event_id", Int64.Type},
            {"timestamp", type datetime},
            {"substation_id", Int64.Type},
            {"event_type_id", Int64.Type},
            {"feed_in_mw", Int64.Type},
            {"curtailed_mw", Int64.Type}
        },
        "en-US"
    )
in
    Typed

// ===== dim_substation =====
let
    Source = GetCsv("dim_substation.csv"),
    Typed = Table.TransformColumnTypes(
        Source,
        {
            {"substation_id", Int64.Type},
            {"substation", type text}
        },
        "en-US"
    )
in
    Typed

// ===== dim_event_type =====
let
    Source = GetCsv("dim_event_type.csv"),
    Typed = Table.TransformColumnTypes(
        Source,
        {
            {"event_type_id", Int64.Type},
            {"event_type", type text},
            {"severity", type text},
            {"severity_rank", Int64.Type}
        },
        "en-US"
    )
in
    Typed

// ===== dq_checks =====
let
    // Violations are reported instead of stopping the refresh, so the report can show them.
    Checks = #table(
        type table [Check = text, Rule = text, Violations = Int64.Type],
        {
            {"Event ID is unique", "No duplicate event_id",
                Table.RowCount(fact_events) - List.Count(List.Distinct(fact_events[event_id]))},
            {"Timestamp is present", "timestamp is not empty",
                Table.RowCount(Table.SelectRows(fact_events, each [timestamp] = null))},
            {"Power is not negative", "feed_in_mw and curtailed_mw >= 0",
                Table.RowCount(Table.SelectRows(fact_events, each [feed_in_mw] < 0 or [curtailed_mw] < 0))},
            {"Curtailment is plausible", "curtailed_mw <= feed_in_mw",
                Table.RowCount(Table.SelectRows(fact_events, each [curtailed_mw] > [feed_in_mw]))},
            {"Substation keys resolve", "fact.substation_id exists in dim_substation",
                List.Count(List.Difference(List.Distinct(fact_events[substation_id]), dim_substation[substation_id]))},
            {"Event type keys resolve", "fact.event_type_id exists in dim_event_type",
                List.Count(List.Difference(List.Distinct(fact_events[event_type_id]), dim_event_type[event_type_id]))}
        }
    ),
    WithStatus = Table.AddColumn(
        Checks, "Status", each if [Violations] = 0 then "PASS" else "FAIL", type text
    )
in
    WithStatus
