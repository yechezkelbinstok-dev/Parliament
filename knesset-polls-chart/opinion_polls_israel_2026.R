# Opinion polls Israel 2026.svg
# Seat projections since the 2022 election, with a LOESS trend line per party.
#
# Needs ggplot2 3.4.x, svglite 2.1.x and the Arial font (newer ggplot2 lays out the legend differently).
# Usage: Rscript opinion_polls_israel_2026.R [polls.csv] [output.svg]

library(ggplot2)
library(svglite)

if (packageVersion("ggplot2") >= "3.5.0" || packageVersion("svglite") >= "2.2.0") {
  warning("Built with ggplot2 3.4.x and svglite 2.1.x; other versions change the layout.")
}
invisible(Sys.setlocale("LC_TIME", "C"))  # English month names on the x axis

args <- commandArgs(trailingOnly = TRUE)
infile  <- if (length(args) >= 1) args[1] else "polls.csv"
outfile <- if (length(args) >= 2) args[2] else "Opinion polls Israel 2026.svg"

# One row per poll, newest first, with the 2022 election result as the last row.
# Seats as published; parties below the threshold as % * 1.2, rounded to 0.1.
polls <- read.csv(infile, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8")
polls$Date <- as.Date(polls$Date)
polls$shape <- ifelse(polls$`Polling firm` == "Election", 23, 19)
polls$size  <- ifelse(polls$`Polling firm` == "Election", 3, 1.5)

# Names as in the column headers of the Wikipedia poll tables.
colours <- c(
  "Likud"            = "#225A9E", "Yesh Atid"     = "#203880", "Blue & White"  = "#0DAAFF",
  "Shas"             = "#000000", "UTJ"           = "#003366", "RZP"           = "#4F9298",
  "Otzma"            = "#FF4500", "Yisrael Beiteinu" = "#9AC0E2", "Ra'am"      = "#15793D",
  "Hadash\u2013Ta'al"     = "#D42436", "Labor"         = "#EE1C25", "Meretz"        = "#40AE49",
  "Balad"            = "#F6600C", "New Hope"      = "#0081B2", "Dems"          = "#2A38D7",
  "Bennett 2026"     = "#44C5BF", "Yashar"        = "#62B9F2", "Reserv."       = "#68692C",
  "Together"         = "#2A2A78", "Unity"         = "#909958", "Amcha Yisrael" = "#8F36BF",
  "Joint List"       = "#01B2AC", "Haredi Public" = "#F5C518"
)
spans <- c(
  "Likud" = 0.2, "Yesh Atid" = 0.2, "Blue & White" = 0.2, "Shas" = 0.2, "UTJ" = 0.2, "RZP" = 0.2,
  "Otzma" = 0.2, "Yisrael Beiteinu" = 0.2, "Ra'am" = 0.2, "Hadash\u2013Ta'al" = 0.2, "Labor" = 0.2,
  "Meretz" = 0.2, "Balad" = 0.2, "New Hope" = 0.4, "Dems" = 0.2, "Bennett 2026" = 0.6,
  "Yashar" = 0.5, "Reserv." = 0.7, "Together" = 0.9, "Unity" = 1.1, "Amcha Yisrael" = 1.1,
  "Joint List" = 1.1, "Haredi Public" = 1.1
)
parties <- names(colours)

last_election <- as.Date("2022-11-01")
next_election <- as.Date("2026-10-27")

p <- ggplot(polls) +
  geom_vline(xintercept = c(last_election, next_election), colour = "#AAAAAA", alpha = 0.73) +
  geom_segment(aes(x = last_election, xend = next_election, y = 4, yend = 4),
               colour = "#666666", alpha = 0.73, linetype = "dashed")

for (party in parties) {
  p <- p + geom_point(aes(Date, .data[[!!party]], shape = I(shape), size = I(size)),
                      colour = colours[[party]], fill = colours[[party]], alpha = 0.33, na.rm = TRUE)
}
for (party in parties) {
  p <- p + geom_smooth(aes(Date, .data[[!!party]], colour = !!party),
                       method = "loess", formula = y ~ x, span = spans[[party]],
                       se = FALSE, n = 1100, linewidth = 1, na.rm = TRUE)
}

p <- p +
  scale_colour_manual(values = colours, breaks = parties) +
  guides(colour = guide_legend(ncol = 1)) +
  scale_x_date(date_breaks = "3 months", date_minor_breaks = "1 month", date_labels = "%b %Y") +
  expand_limits(y = 0) +
  labs(x = "", y = "Seats", colour = "") +
  theme(text = element_text(family = "Arial"),
        axis.text.y = element_text(size = 12),
        axis.text.x = element_text(size = 11),
        axis.title.y = element_text(size = 16),
        legend.text = element_text(size = 16),
        legend.key.width = unit(24, "pt"),
        legend.key.height = unit(22, "pt"))

svglite(outfile, width = 18, height = 8)
print(p)
invisible(dev.off())

# Commons' renderer ignores svglite's scoped CSS, so unscope it; Windows line endings.
svg <- readLines(outfile)
svg <- gsub(".svglite ", "", svg, fixed = TRUE)
con <- file(outfile, "wb")
writeLines(svg, con, sep = "\r\n")
close(con)
