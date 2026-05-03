<?php
/* This file is part of Holmes MCP.
 * Holmes MCP is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Holmes MCP is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 */

function holmesMcp_install() {
    config::save('port', 8765, 'holmesMcp');
}

function holmesMcp_update() {
}

function holmesMcp_remove() {
    holmesMcp::deamon_stop();
}
