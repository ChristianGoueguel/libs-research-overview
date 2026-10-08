# Read-only extraction of the soil-texture results used in the slides (nothing is re-trained).
# Usage: Rscript scripts/extract_soil_results.R path/to/Granulo_pls_enet.RData
# Requires: caret, pls, glmnet, jsonlite. Writes data/soil-texture/{results.json,coefs.json,wavelength-calibration.csv}.
args <- commandArgs(TRUE)
if (!length(args)) stop("usage: Rscript scripts/extract_soil_results.R path/to/Granulo_pls_enet.RData")
rdata <- path.expand(args[1])
OUT <- "data/soil-texture"; dir.create(OUT, showWarnings = FALSE, recursive = TRUE)
Sys.setenv(OUT = OUT)
suppressPackageStartupMessages({library(caret); library(glmnet); library(pls); library(jsonlite)})
load(rdata)
te <- setdiff(seq_len(nrow(RAWdata)), as.integer(inTrain[,1]))
k <- 0.54; back <- function(x) pmax(x, 0)^(1/k)
fr <- c("sand", "silt", "clay")
mods <- list(PLSR = list(sand = pls_sand, silt = pls_silt, clay = pls_clay), ENET = list(sand = enet_sand, silt = enet_silt, clay = enet_clay))
out <- list(tune = list(), test = list(), resample = list(), internals = list())
for (f in fr) {
  r <- mods$PLSR[[f]]$results
  out$tune$PLSR[[f]] <- list(ncomp = r$ncomp, RMSE = round(r$RMSE, 4), RMSESD = round(r$RMSESD, 4), R2 = round(r$Rsquared, 4), best = mods$PLSR[[f]]$bestTune$ncomp)
  e <- mods$ENET[[f]]$results; curves <- list()
  for (a in sort(unique(e$alpha))) { d <- e[e$alpha == a, ]; d <- d[order(d$lambda), ]
    keep <- unique(round(seq(1, nrow(d), length.out = min(nrow(d), 100))))
    curves[[length(curves) + 1]] <- list(alpha = a, lambda = signif(d$lambda[keep], 5), RMSE = round(d$RMSE[keep], 4)) }
  out$tune$ENET[[f]] <- list(curves = curves, bestAlpha = mods$ENET[[f]]$bestTune$alpha, bestLambda = mods$ENET[[f]]$bestTune$lambda)
  o <- if (f == "clay") RAWdata$Clay[te] else get(paste0(f, "Test"))
  pp <- lapply(mods, function(m) { p <- predict(m[[f]], spectraTest); if (f == "clay") back(p) else p })
  out$test[[f]] <- list(sample = as.character(RAWdata$Sample[te]), obs = round(o, 2), PLSR = round(pp$PLSR, 2), ENET = round(pp$ENET, 2))
  for (m in names(mods)) out$resample[[m]][[f]] <- round(mods[[m]][[f]]$resample$RMSE, 4)
}
X <- as.matrix(RAWdata[, grep("^V[0-9]+$", names(RAWdata))])
coefs <- list(meanSpectrum = round(colMeans(X), 1))
for (f in fr) {
  pm <- mods$PLSR[[f]]; nc <- pm$bestTune$ncomp; fm <- pm$finalModel
  W <- fm$loading.weights[, 1:nc, drop = FALSE]; Tt <- fm$scores[, 1:nc, drop = FALSE]; Q <- fm$Yloadings[1, 1:nc]
  ss <- Q^2 * colSums(Tt^2); Wn <- sweep(W, 2, sqrt(colSums(W^2)), "/")
  vip <- sqrt(nrow(W) * drop(Wn^2 %*% ss) / sum(ss))
  em <- mods$ENET[[f]]; cf <- as.matrix(coef(em$finalModel, s = em$finalModel$lambdaOpt))[-1, 1]
  coefs[[f]] <- list(PLSR = signif(drop(coef(fm, ncomp = nc)), 4), ENET = signif(cf, 4), VIP = round(vip, 3))
  out$internals[[f]] <- list(ncomp = nc, Xvar = round(sum(100 * fm$Xvar[1:nc] / fm$Xtotvar), 1), nonzero = sum(cf != 0),
                             alpha = em$bestTune$alpha, lambda = em$bestTune$lambda, nVIPgt1 = sum(vip > 1))
}
str(out$internals)
write_json(out, file.path(Sys.getenv("OUT"), "results.json"), auto_unbox = TRUE, digits = NA)
write_json(coefs, file.path(Sys.getenv("OUT"), "coefs.json"), auto_unbox = TRUE, digits = NA)
cat("ok\n")

# --- Wavelength calibration of the 7,152 spectral variables (cubic fit on 11 isolated reference lines) ---
X <- as.matrix(RAWdata[, grep("^V[0-9]+$", names(RAWdata))]); ms <- colMeans(X); n <- length(ms)
peak <- function(guess, win) {
  r <- max(2, round(guess - win)):min(n - 1, round(guess + win)); i <- r[which.max(ms[r])]
  y0 <- ms[i-1]; y1 <- ms[i]; y2 <- ms[i+1]; i + 0.5 * (y0 - y2) / (y0 - 2*y1 + y2)
}
inv <- function(w, f) uniroot(function(i) f(i) - w, c(-500, n + 500))$root
lines_all <- c("Si I 251.611" = 251.611, "Si I 252.851" = 252.851, "Mg II 279.553" = 279.553, "Mg II 280.271" = 280.271,
  "Mg I 285.213" = 285.213, "Si I 288.158" = 288.158, "Al I 308.215" = 308.215, "Al I 309.271" = 309.271,
  "Ca II 315.887" = 315.887, "Ca II 317.933" = 317.933, "Ti II 334.941" = 334.941, "Mg I 383.829" = 383.829,
  "Ca II 393.366" = 393.366, "Al I 394.401" = 394.401, "Al I 396.152" = 396.152, "Ca II 396.847" = 396.847,
  "Fe I 404.581" = 404.581, "Sr II 407.771" = 407.771, "Ca I 422.673" = 422.673, "Ca I 445.478" = 445.478,
  "Ba II 455.403" = 455.403, "Mg I 517.268" = 517.268, "Mg I 518.361" = 518.361, "Na I 588.995" = 588.995,
  "Na I 589.592" = 589.592, "H I 656.279" = 656.279, "Li I 670.78" = 670.78, "K I 766.490" = 766.490,
  "K I 769.896" = 769.896, "O I 777.194" = 777.194)
anchorsN <- c("Mg I 285.213", "Si I 288.158", "Al I 308.215", "Al I 309.271", "Ca II 393.366", "Ca II 396.847", "Ca I 422.673", "Na I 588.995", "Li I 670.78", "K I 766.490", "K I 769.896")
f <- function(i) 279.553 + (i - 950) * (393.366 - 279.553) / (2298 - 950)
for (it in 1:4) {
  pos <- sapply(lines_all[anchorsN], function(w) peak(inv(w, f), win = c(30, 6, 4, 4)[it]))
  fit <- lm(w ~ poly(i, 3, raw = TRUE), data = data.frame(w = lines_all[anchorsN], i = pos))
  f <- local({ ff <- fit; function(i) predict(ff, data.frame(i = i)) })
}
allpos <- sapply(lines_all, function(w) peak(inv(w, f), win = 3))
tab <- data.frame(line = names(lines_all), anchor = names(lines_all) %in% anchorsN, idx = round(allpos, 1),
                  resid_nm = round(lines_all - f(allpos), 3), height = round(ms[round(allpos)]))
print(tab, row.names = FALSE)
cat("RMS anchors:", round(sqrt(mean(tab$resid_nm[tab$anchor]^2)), 3), " RMS validation:", round(sqrt(mean(tab$resid_nm[!tab$anchor]^2)), 3), "nm\n")
loo <- sapply(seq_along(anchorsN), function(j) { fj <- lm(w ~ poly(i, 3, raw = TRUE), data = data.frame(w = lines_all[anchorsN][-j], i = pos[-j])); lines_all[anchorsN][j] - predict(fj, data.frame(i = pos[j])) })
cat("LOO residuals:", round(loo, 3), "\n")
cat("range:", round(f(1), 2), "–", round(f(n), 2), "\n")
write.csv(data.frame(index = 1:n, wavelength = round(f(1:n), 3)), file.path(Sys.getenv("OUT"), "wavelength-calibration.csv"), row.names = FALSE)
