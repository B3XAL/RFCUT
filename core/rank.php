<?php
$target = ord('>'); // 62

$results = [];

while (($line = fgets(STDIN)) !== false) {
    if (preg_match('/After:\s+.*<script(.)(.*)$/u', $line, $m)) {
        $char = $m[1];
        $code = mb_ord($char, 'UTF-8');
        $dist = abs($code - $target);
        $results[] = [$dist, $code, $char, trim($line)];
    }
}

usort($results, fn($a,$b) => $a[0] <=> $b[0]);

foreach ($results as [$d,$c,$ch,$raw]) {
    printf("Δ=%-4d  U+%04X  [%s]  %s\n", $d, $c, $ch, $raw);
}
