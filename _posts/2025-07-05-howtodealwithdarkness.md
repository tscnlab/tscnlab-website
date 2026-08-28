---
layout: post
title: "Ever wondered how to deal with darkness?"
date: 2025-07-05
author: "Erina Tsukimori"
excerpt_text: "Modeling and Visualization of Zero-Inflated Personal Light Exposure Data on a Logarithmic Scale"
source_url: "https://www.tscnlab.org/news/howtodealwithdarkness"
image: "/assets/images/news/howtodealwithdarkness-featured-01.jpg"
---

<figure class="article-figure">
  <img src="{{ '/assets/images/news/howtodealwithdarkness-inline-01.jpg' | relative_url }}" alt="">
</figure>

<p>A new publication from our Dr Johannes Zauner addresses a critical methodological challenge in circadian and myopia research: how to properly handle zero-lux measurements that routinely occur in personal light exposure studies.</p>

<p>Zero-lux readings matter. In free-living light measurements, true zeros routinely occur and can't simply be dropped or ignored when applying log-based analyses. When people sleep, move through windowless spaces, or spend time under covers, these darkness periods contain important information about light exposure patterns.</p>

<p>Our research compared different approaches to visualizing and modelling this zero-inflated light data. We tested four visualization scales and three modelling strategies to find the best ways to handle these challenging but crucial measurements.</p>

<p>Key findings:</p>

<p>Symlog transformations are best for visualization, showing zero-lux values while preserving the full dynamic range from very low to very high light exposures Adding –1 log₁₀ lux to zero readings allows robust statistical modelling on logarithmic scales Tweedie models offer a unified solution that handles zeros and skew without requiring data transformation</p>

<p>The methods extend beyond light exposure research to other biological rhythm data that exhibit zero inflation, such as accelerometery in sleep studies or activity monitoring in animal models.</p>

<p>LightLogR: your toolbox for zero-inflated light data. Our open-source R package LightLogR implements these visualization and modelling solutions, ready for circadian, sleep, and myopia researchers to deploy.</p>

<p>Proper treatment of darkness and low-light exposures is critical for understanding human circadian entrainment, light-related health outcomes, and myopia development under real-world conditions.</p>

<p>https://journals.sagepub.com/doi/10.1177/07487304251336624</p>
