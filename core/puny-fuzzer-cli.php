<?php
require 'vendor/autoload.php';

use Algo26\IdnaConvert\ToUnicode;

ini_set('display_errors', '1');
error_reporting(E_ERROR | E_PARSE);
set_time_limit(0);

// --------------------
// Help system
// --------------------

$argv = $_SERVER['argv'];
$argc = $_SERVER['argc'];

if (
    $argc === 1 ||
    in_array('-h', $argv, true) ||
    in_array('--help', $argv, true)
) {
    showHelp();
    exit(0);
}

// --------------------
// Options
// --------------------

$options = getopt("", ["before:", "matches:", "contains:", "randomPad"]);

$before    = $options['before']   ?? "x@xn--script-\$c1\$1\$2\$3";
$matches   = $options['matches']  ?? "@<script@";
$contains  = $options['contains'] ?? "@[<]@";
$randomPad = isset($options['randomPad']);

// --------------------
// Fuzzer
// --------------------

$IDN = new ToUnicode();

$chrs = array_merge(range('a','z'),range('A','Z'));
$whitespace = [" ","\t","\r","\n"];

echo "Starting fuzzing...\n";

while (true) {

    if ($randomPad) {
        for ($i=1;$i<=9;$i++) $pad[$i] = random_int(0,5);
    } else {
        for ($i=1;$i<=9;$i++) $pad[$i] = 0;
    }

    for ($i=1;$i<=9;$i++) {
        $int[$i] = str_pad(random_int(0,9), $pad[$i], "0", STR_PAD_LEFT);
        $chr[$i] = $chrs[array_rand($chrs)];
    }

    $w1 = $whitespace[array_rand($whitespace)];
    $w2 = $whitespace[array_rand($whitespace)];

    $input = $before;

    for ($i=1;$i<=9;$i++) {
        $input = str_replace("\$$i", $int[$i], $input);
        $input = str_replace("\$c$i", $chr[$i], $input);
    }

    $input = str_replace('$w1', $w1, $input);
    $input = str_replace('$w2', $w2, $input);

    try {
        $after = $IDN->convertEmailAddress($input);
    } catch (Throwable $e) {
        continue;
    }

    $payload = substr($after,2);

    if (preg_match($matches, $payload)) {
        echo "\n🔥 MATCH FOUND\n";
        echo "Input:  $input\n";
        echo "After:  $after\n";
        exit;
    }

    if (preg_match($contains, $payload) && !str_contains($after, "xn--")) {
        echo "\n⚠️  CONTAINS FOUND\n";
        echo "Input:  $input\n";
        echo "After:  $after\n";
    }
}


// --------------------
// Help function
// --------------------

function showHelp(): void
{
    $script = basename(__FILE__);

    echo <<<HELP

    Puny Fuzzer CLI

Usage:
  php $script [options]

Example:
  php core/$script \\
    --before='x@xn--poc-\$c1\$c2\$1\$2' \\
    --matches='@<@' \\
    --contains='@<poc@'

Options:
  --before     Input template
  --matches    Matching regular expression
  --contains   Containment regular expression
  --randomPad  Random numeric padding

Help:
  -h, --help   Display this help message

HELP;
}
