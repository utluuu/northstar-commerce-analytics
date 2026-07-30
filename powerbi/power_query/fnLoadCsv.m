(fileName as text, columnTypes as list) as table =>
let
    Source = Csv.Document(
        File.Contents(CsvRoot & "\\" & fileName),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, columnTypes, "en-US")
in
    TypedColumns
