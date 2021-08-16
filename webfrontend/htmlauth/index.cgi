#!/usr/bin/perl

# Copyright 2019-2020 Michael Schlenstedt, michael@loxberry.de
#                     Christian Fenzl, christian@loxberry.de
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


##########################################################################
# Modules
##########################################################################

# use Config::Simple '-strict';
# use CGI::Carp qw(fatalsToBrowser);
use CGI;
use LoxBerry::System;
# use LoxBerry::Web;
use LoxBerry::JSON; # Available with LoxBerry 2.0
#require "$lbpbindir/libs/LoxBerry/JSON.pm";
use LoxBerry::Log;
use Time::HiRes qw ( sleep );
use warnings;
use strict;
#use Data::Dumper;

##########################################################################
# Variables
##########################################################################

my $log;

# Read Form
my $cgi = CGI->new;
my $q = $cgi->Vars;

my $version = LoxBerry::System::pluginversion();
my $template;

# Language Phrases
my %L;

# Globals 
my $CFGFILE = $lbpconfigdir . "/config.json";

##########################################################################
# AJAX
##########################################################################

# Prevent reading configs from others
system("chmod 0600 $lbpconfigdir/*.json");

if( $q->{ajax} ) {
	
	## Logging for ajax requests
	#$log = LoxBerry::Log->new (
	#	name => 'AJAX',
	#	filename => "$lbplogdir/ajax.log",
	#	stderr => 1,
	#	loglevel => 7,
	#	addtime => 1,
	#	append => 1,
	#	nosession => 1,
	#);
	
	LOGSTART "P$$ Ajax call: $q->{ajax}";
	LOGDEB "P$$ Request method: " . $ENV{REQUEST_METHOD};
	
	## Handle all ajax requests 
	#require JSON;
	# require Time::HiRes;
	my %response;
	ajax_header();

	# CheckSecPin (WebUI SecPin Question)
	if( $q->{ajax} eq "checksecpin" ) {
		LOGINF "P$$ checksecpin: CheckSecurePIN was called.";
		$response{error} = &checksecpin();
		print JSON->new->canonical(1)->encode(\%response);
		exit();
	}

	# All other requests need to send the SecPIN
	if($ENV{REQUEST_METHOD}) {
		LOGINF "P$$ Remote request - checking SecurePIN";
		my $seccheck = LoxBerry::System::check_securepin($q->{secpin});
		if($seccheck) {
			LOGERR "P$$ SecurePIN error: $seccheck";
			$response{error} = $seccheck;
			$response{secpinerror} = 1;
			$response{message} = "SecurePIN invalid";
			print JSON->new->canonical(1)->encode(\%response);
			exit(1);
		} else {
			LOGINF "P$$ SecurePIN ok";
		}
	}
	
	# get sc2mqtt status
	if( $q->{ajax} eq "getstate" ) {
		LOGINF "P$$ getstate: getstate was called.";
		$response{pidof} = &getstate();
		if (!$response{pidof}) {
			$response{error} = 1;
		}
		print JSON->new->canonical(1)->encode(\%response);
	}
	
	# Save MQTT Settings
	if( $q->{ajax} eq "savemqtt" ) {
		LOGINF "P$$ savemqtt: savemqtt was called.";
		$response{error} = &savemqtt();
		print JSON->new->canonical(1)->encode(\%response);
	}
	
	# Save SKConnect Settings
	if( $q->{ajax} eq "saveskconnect" ) {
		LOGINF "P$$ saveskconnect: saveskconnect was called.";
		$response{error} = &saveskconnect();
		print JSON->new->canonical(1)->encode(\%response);
	}
	
	# Get config
	if( $q->{ajax} eq "getconfig" ) {
		LOGINF "P$$ getconfig: Getconfig was called.";
		my $content;
		if ( !$q->{config} ) {
			LOGINF "P$$ getconfig: No config given.";
			$response{error} = "1";
			$response{message} = "No config given";
		}
		elsif ( &checksecpin() ) {
			LOGINF "P$$ getconfig: Wrong SecurePIN.";
			$response{error} = "1";
			$response{message} = "Wrong SecurePIN";
		}
		elsif ( !-e $lbpconfigdir . "/" . $q->{config} . ".json" ) {
			LOGINF "P$$ getconfig: Config file does not exist.";
			$response{error} = "1";
			$response{message} = "Config file does not exist";
		}
		else {
			# Config
			my $cfgfile = $lbpconfigdir . "/" . $q->{config} . ".json";
			LOGINF "P$$ Parsing Config: " . $cfgfile;
			$content = LoxBerry::System::read_file("$cfgfile");
			print $content;
		}
		print JSON->new->canonical(1)->encode(\%response) if !$content;
	}
	
	exit;

##########################################################################
# Normal request (not AJAX)
##########################################################################

} else {
	
	require LoxBerry::Web;
	
	## Logging for serverside webif requests
	#$log = LoxBerry::Log->new (
	#	name => 'Webinterface',
	#	filename => "$lbplogdir/webinterface.log",
	#	stderr => 1,
	#	loglevel => 7,
	#	addtime => 1
	#);

	LOGSTART "SkodaConnect WebIf";
	
	# Init Template
	$template = HTML::Template->new(
	    filename => "$lbptemplatedir/settings.html",
	    global_vars => 1,
	    loop_context_vars => 1,
	    die_on_bad_params => 0,
	);
	%L = LoxBerry::System::readlanguage($template, "language.ini");
	
	# Default is SkodaConnect form
	$q->{form} = "skconnect" if !$q->{form};

	if ($q->{form} eq "skconnect") { &form_skconnect() }
	elsif ($q->{form} eq "mqtt") { &form_mqtt() }
	elsif ($q->{form} eq "log") { &form_log() }

	# Print the form
	&form_print();
}

exit;


##########################################################################
# Form: BRIDGES
##########################################################################

sub form_skconnect
{
	$template->param("FORM_SKCONNECT", 1);
	return();
}


##########################################################################
# Form: MQTT
##########################################################################

sub form_mqtt
{
	$template->param("FORM_MQTT", 1);
	my $mqttplugindata = LoxBerry::System::plugindata("mqttgateway");
	$template->param("MQTTGATEWAY_INSTALLED", 1) if ( $mqttplugindata );
	$template->param("MQTTGATEWAY_PLUGINDBFOLDER", $mqttplugindata->{PLUGINDB_FOLDER}) if ( $mqttplugindata );
	return();
}


##########################################################################
# Form: Log
##########################################################################

sub form_log
{
	$template->param("FORM_LOG", 1);
	$template->param("LOGLIST", LoxBerry::Web::loglist_html());
	return();
}

##########################################################################
# Print Form
##########################################################################

sub form_print
{
	# Navbar
	our %navbar;

	$navbar{10}{Name} = "$L{'COMMON.LABEL_SKCONNECT'}";
	$navbar{10}{URL} = 'index.cgi?form=skconnect';
	$navbar{10}{active} = 1 if $q->{form} eq "skconnect";
	
	$navbar{30}{Name} = "$L{'COMMON.LABEL_MQTT'}";
	$navbar{30}{URL} = 'index.cgi?form=mqtt';
	$navbar{30}{active} = 1 if $q->{form} eq "mqtt";
	
	$navbar{99}{Name} = "$L{'COMMON.LABEL_LOG'}";
	$navbar{99}{URL} = 'index.cgi?form=log';
	$navbar{99}{active} = 1 if $q->{form} eq "log";
	
	# Template
	LoxBerry::Web::lbheader($L{'COMMON.LABEL_PLUGINTITLE'} . " V$version", "https://www.loxwiki.eu/x/CIGzB", "");
	print $template->output();
	LoxBerry::Web::lbfooter();
	
	exit;

}


######################################################################
# AJAX functions
######################################################################

sub ajax_header
{
	print $cgi->header(
			-type => 'application/json',
			-charset => 'utf-8',
			-status => '200 OK',
	);	
}	

sub checksecpin
{
	my $error;
	if ( LoxBerry::System::check_securepin($q->{secpin}) ) {
		LOGINF "P$$ checksecpin: The entered securepin is wrong.";
		$error = 1;
	} else {
		LOGINF "P$$ checksecpin: You have entered the correct securepin. Continuing.";
		$error = 0;
	}
	return ($error);
}

sub savemqtt
{
	my $errors;
	my $jsonobj = LoxBerry::JSON->new();
	my $jsonobjcred = LoxBerry::JSON->new();
	my $jsonobjcfg = LoxBerry::JSON->new();
	my $mqttplugindata = LoxBerry::System::plugindata("mqttgateway");
	my $cfg = $jsonobj->open(filename => $CFGFILE);
	$cfg->{topic} = $q->{topic};
	$cfg->{usemqttgateway} = $q->{usemqttgateway};
	# Get MQTT Gateway credentials
	if ( is_enabled($q->{usemqttgateway}) ) {
		my $gwcred = $jsonobjcred->open(filename => $lbhomedir . "/config/plugins/" . $mqttplugindata->{PLUGINDB_FOLDER} . "/cred.json");
		$q->{brokeruser} = $gwcred->{Credentials}->{brokeruser};
		$q->{brokerpassword} = $gwcred->{Credentials}->{brokerpass};
		my $gwcfg = $jsonobjcfg->open(filename => $lbhomedir . "/config/plugins/" . $mqttplugindata->{PLUGINDB_FOLDER} . "/mqtt.json");
		if ( $gwcfg->{Main}->{brokeraddress} =~ /:/ ) {
			my ($broker,$port) = split (/:/,$gwcfg->{Main}->{brokeraddress});
			$q->{broker} = $broker;
			$q->{brokerport} = $port;
		} else {
			$q->{broker} = $gwcfg->{Main}->{brokeraddress};
			$q->{brokerport} = "1883";
		};
	};
	$cfg->{broker} = $q->{broker};
	$cfg->{brokerport} = $q->{brokerport};
	$cfg->{brokeruser} = $q->{brokeruser};
	$cfg->{brokerpassword} = $q->{brokerpassword};
	if ( $q->{brokeruser} && $q->{brokerpassword} ) {
		$cfg->{brokerauth} = "1";
	} else {
		$cfg->{brokerauth} = "0";
	}
	$jsonobj->write();
	
	# Save mqtt_subscriptions.cfg for MQTT Gateway
	my $subscr_file = $lbpconfigdir."/mqtt_subscriptions.cfg";
	eval {
		open(my $fh, '>', $subscr_file);
		print $fh $q->{topic} . "/#\n";
		close $fh;
	};
	if ($@) {
		LOGERR "savemqtt: Could not write $subscr_file: $@";
	}

	# Restart sc2mqtt
	system ("$lbpbindir/wrapper.sh restart > /dev/null 2>&1");

	return ($errors);
}

sub saveskconnect
{
	my $errors;
	my $jsonobj = LoxBerry::JSON->new();
	my $cfg = $jsonobj->open(filename => $CFGFILE);
	$cfg->{user} = $q->{user};
	$cfg->{password} = $q->{password};
	$jsonobj->write();
	
	# Restart sc2mqtt
	system ("$lbpbindir/wrapper.sh restart > /dev/null 2>&1");

	return ($errors);
}

sub getstate
{
	my $pid = qx (pgrep -f $lbpbindir/sclooper.sh);
	chomp($pid);;
	return ($pid);
}

END {
	if($log) {
		LOGEND;
	}
}

