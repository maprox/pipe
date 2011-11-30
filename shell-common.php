<?php

/**
 * Arguments parsing
 * @param array $argv
 * @return array
 */
function arguments($argv)
{
	$_ARG = array('input' => array());
	// First param is this scripts name. Not needed.
	array_shift($argv);
	foreach ($argv as $arg)
	{
		if (preg_match('#^-{1,2}([a-zA-Z0-9]*)=?(.*)$#', $arg, $matches))
		{
			$key = $matches[1];
			switch ($matches[2])
			{
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
		}
		else
		{
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
	$files = glob(WORKING_DIR . "conf/serv-*.conf");
	$return = array();

	foreach ($files as $file)
	{
		$key = array();
		preg_match('/conf\/serv-(.*)\.conf/ui', $file, $key);

		$data = file($file);

		foreach ($data as $line)
		{
			if (preg_match('/^port=(\d+)/', $line, $port))
			{
				$return[$key[1]] = $port[1];
				break;
			}
		}
	}

	return $return;
}

/**
 * Parses conf files of given protocols and returns array
 * @return array
 */
function getTrackers($names, $port = false)
{
	$return = array();
	foreach ($names as $name)
	{
		$file = WORKING_DIR . "conf/serv-$name.conf";
		if (file_exists($file))
		{
			if ($port && count($names) == 1)
			{
				$return[$name] = $port;
				continue;
			}

			$data = file($file);

			foreach ($data as $line)
			{
				if (preg_match('/^port=(\d+)/', $line, $port))
				{
					$return[$name] = $port[1];
					break;
				}
			}
		}
	}

	return $return;
}
