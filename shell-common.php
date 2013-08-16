<?php

/**
 * Returns true if script is running on linux machine
 * @return bool
 */
function isLinux()
{
	return function_exists('posix_getuid');
}

/**
 * Arguments parsing
 * @param array $argv
 * @return array
 */
function arguments($argv)
{
	$_ARG = array('input' => array());
	// First param is this scripts name..
	$_ARG['name'] = array_shift($argv);
	foreach ($argv as $arg) {
		if (preg_match('#^-{1,2}([a-zA-Z0-9]*)=?(.*)$#', $arg, $matches)) {
			$key = $matches[1];
			switch ($matches[2]) {
				case '':
				case 'true':
					$arg = true;
					break;
				case 'false':
					$arg = false;
					break;
				default:
					$arg = $matches[2];
			}
			$_ARG[$key] = $arg;
		} else {
			$_ARG['input'][] = $arg;
		}
	}
	return $_ARG;
}

/**
 * Parses all conf files and returns array of protocols
 * @return array
 */
function getAllTrackers()
{
	$files = glob(WORKING_DIR . "conf/handlers/*.conf");
	$return = array();
	foreach ($files as $file) {
		preg_match('/conf\/handlers\/(.*)\.conf/ui', $file, $key);
		$name = $key[1];
		$return[$name] = readTrackerConfig($name);
	}
	$return['balancer'] = readTrackerConfig('balancer');
	return array_filter($return);
}

/**
 * Parses conf files of given protocols and returns array
 * @return array
 */
function getTrackers($names, $port = false)
{
	$return = array();
	foreach ($names as $name) {
		$return[$name] = readTrackerConfig($name, $port);
	}
	return array_filter($return);
}

/**
 * Processes conf file of given protocol
 * @return array
 */
function readTrackerConfig($name, $port = false)
{
	if ($name == 'balancer') {
		return array(
			'port' => 0,
			'pipeconf' => getPipeConf('balancer')
		);
	}

	$file = WORKING_DIR . "conf/handlers/$name.conf";
	if (!file_exists($file)) { return false; }

	$return = array('pipeconf' => getPipeConf($name));

	if ($port) {
		$return['port'] = $port;
	} else {
		$return['port'] = readIni($file, 'port');
	}

	return $return['port'] ? $return : false;
}

/**
 * Reads option from ini file
 * There was a problem with parse_ini function
 * @return string
 */
function readIni($file, $option)
{
	$data = file($file);
	foreach ($data as $line) {
		if (preg_match('/^' . $option . '=(.*)/', trim($line), $config)) {
			return $config[1];
		}
	}
	return null;
}

/**
 * Finds pipe configuration file
 */
function getPipeConf($name)
{
	$file = WORKING_DIR . "conf/pipe-$name.conf";
	if (file_exists($file)) {
		return "conf/pipe-$name.conf";
	}

	$file = WORKING_DIR . "conf/pipe-default.conf";
	if (file_exists($file)) {
		return "conf/pipe-default.conf";
	}

	return "conf/pipe.conf";
}

/**
 * Starts command in background
 * @param string $command
 */
function startInBackground($command)
{
	shell_exec("nohup $command > /dev/null 2>&1");
}
