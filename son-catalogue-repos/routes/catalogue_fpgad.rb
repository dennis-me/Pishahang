##
## Copyright (c) 2015 SONATA-NFV
## ALL RIGHTS RESERVED.
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##
## Neither the name of the SONATA-NFV
## nor the names of its contributors may be used to endorse or promote
## products derived from this software without specific prior written
## permission.
##
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the SONATA
## partner consortium (www.sonata-nfv.eu).

# @see SonCatalogue

class CatalogueV2 < SonataCatalogue
  ### FPGAD API METHODS ###

  # @method get_fpgads
  # @overload get '/catalogues/fpgads/?'
  #	Returns a list of FPGADs
  # -> List many descriptors
  get '/fpgads/?' do
    params['offset'] ||= DEFAULT_OFFSET
    params['limit'] ||= DEFAULT_LIMIT
    logger.info "Catalogue: entered GET /api/v2/fpgads?#{query_string}"

    # Split keys in meta_data and data
    # Then transform 'string' params Hash into keys
    keyed_params = add_descriptor_level('fpgad', params)

    # Set headers
    case request.content_type
      when 'application/x-yaml'
        headers = { 'Accept' => 'application/x-yaml', 'Content-Type' => 'application/x-yaml' }
      else
        headers = { 'Accept' => 'application/json', 'Content-Type' => 'application/json' }
    end
    headers[:params] = params unless params.empty?

    # Get rid of :offset and :limit
    [:offset, :limit].each { |k| keyed_params.delete(k) }

    # Check for special case (:version param == last)
    if keyed_params.key?(:'fpgad.version') && keyed_params[:'fpgad.version'] == 'last'
      keyed_params.delete(:'fpgad.version')

      fpgads = Fpsd.where((keyed_params)).sort({ 'fpgad.version' => -1 }) #.limit(1).first()
      logger.info "Catalogue: FPGADs=#{fpgads}"

      if fpgads && fpgads.size.to_i > 0
        logger.info "Catalogue: leaving GET /api/v2/fpgads?#{query_string} with #{fpgads}"

        fpgads_list = []
        checked_list = []

        fpgads_name_vendor = Pair.new(fpgads.first.fpgad['name'], fpgads.first.fpgad['vendor'])
        checked_list.push(fpgads_name_vendor)
        fpgads_list.push(fpgads.first)

        fpgads.each do |fpgad|
          if (fpgad.fpgad['name'] != fpgads_name_vendor.one) || (fpgad.fpgad['vendor'] != fpgads_name_vendor.two)
            fpgads_name_vendor = Pair.new(fpgad.fpgad['name'], fpgad.fpgad['vendor'])
          end
          fpgads_list.push(fpgad) unless checked_list.any? { |pair| pair.one == fpgads_name_vendor.one &&
              pair.two == fpgads_name_vendor.two }
          checked_list.push(fpgads_name_vendor)
        end
      else
        logger.info "Catalogue: leaving GET /api/v2/fpgads?#{query_string} with 'No FPGADs were found'"
        fpgads_list = []

      end
      fpgads = apply_limit_and_offset(fpgads_list, offset=params[:offset], limit=params[:limit])

    else
      # Do the query
      fpgads = Fpsd.where(keyed_params)
      # Set total count for results
      headers 'Record-Count' => fpgads.count.to_s
      logger.info "Catalogue: FPGADs=#{fpgads}"
      if fpgads && fpgads.size.to_i > 0
        logger.info "Catalogue: leaving GET /api/v2/fpgads?#{query_string} with #{fpgads}"
        # Paginate results
        fpgads = fpgads.paginate(offset: params[:offset], limit: params[:limit])
      else
        logger.info "Catalogue: leaving GET /api/v2/fpgads?#{query_string} with 'No FPGADs were found'"
      end
    end

    response = ''
    case request.content_type
      when 'application/json'
        response = fpgads.to_json
      when 'application/x-yaml'
        response = json_to_yaml(fpgads.to_json)
      else
        halt 415
    end
    halt 200, {'Content-type' => request.content_type}, response
  end

  # @method get_fpgads_id
  # @overload get '/catalogues/fpgads/:id/?'
  #	  GET one specific descriptor
  #	  @param :id [Symbol] id FPGAD ID
  # Show a FPGAD by internal ID (uuid)
  get '/fpgads/:id/?' do
    unless params[:id].nil?
      logger.debug "Catalogue: GET /api/v2/fpgads/#{params[:id]}"

      begin
        fpgad = Fpsd.find(params[:id])
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "The FPGAD ID #{params[:id]} does not exist" unless fpgad
      end
      logger.debug "Catalogue: leaving GET /api/v2/fpgads/#{params[:id]}\" with FPGAD #{fpgad}"

      response = ''
      case request.content_type
        when 'application/json'
          response = fpgad.to_json
        when 'application/x-yaml'
          response = json_to_yaml(fpgad.to_json)
        else
          halt 415
      end
      halt 200, {'Content-type' => request.content_type}, response

    end
    logger.debug "Catalogue: leaving GET /api/v2/fpgads/#{params[:id]} with 'No FPGAD ID specified'"
    json_error 400, 'No FPGAD ID specified'
  end

  # @method post_fpgads
  # @overload post '/catalogues/fpgads'
  # Post a FPGAD in JSON or YAML format
  post '/fpgads' do
    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    # Compatibility support for YAML content-type
    case request.content_type
      when 'application/x-yaml'
        # Validate YAML format
        # When updating a FGPAD, the json object sent to API must contain just data inside
        # of the fpgad, without the json field fpgad: before
        fpga, errors = parse_yaml(request.body.read)
        halt 400, errors.to_json if errors

        # Translate from YAML format to JSON format
        new_fpga_json = yaml_to_json(fpga)

        # Validate JSON format
        new_fpga, errors = parse_json(new_fpga_json)
        halt 400, errors.to_json if errors

      else
        # Compatibility support for JSON content-type
        # Parses and validates JSON format
        new_fpga, errors = parse_json(request.body.read)
        halt 400, errors.to_json if errors
    end

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    # Validate FPGAD
    json_error 400, 'ERROR: FPGAD Vendor not found' unless new_fpga.has_key?('vendor')
    json_error 400, 'ERROR: FPGAD Name not found' unless new_fpga.has_key?('name')
    json_error 400, 'ERROR: FPGAD Version not found' unless new_fpga.has_key?('version')

    # Check if FPGAD already exists in the catalogue by name, vendor and version
    begin
      fpga = Fpsd.find_by({ 'fpgad.name' => new_fpga['name'], 'fpgad.vendor' => new_fpga['vendor'],
                           'fpgad.version' => new_fpga['version'] })
      json_return 200, 'Duplicated FPGAD Name, Vendor and Version'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    # Check if FPGAD has an ID (it should not) and if it already exists in the catalogue
    begin
      fpga = Fpsd.find_by({ '_id' => new_fpga['_id'] })
      json_return 200, 'Duplicated FPGAD ID'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    if keyed_params.key?(:username)
      username = keyed_params[:username]
    else
      username = nil
    end

    # Save to DB
    begin
      new_fpgad = {}
      new_fpgad['fpgad'] = new_fpga
      # Generate the UUID for the descriptor
      new_fpgad['_id'] = SecureRandom.uuid
      new_fpgad['status'] = 'active'
      new_fpgad['signature'] = nil
      new_fpgad['md5'] = checksum new_fpga.to_s
      new_fpgad['username'] = username
      fpga = Fpsd.create!(new_fpgad)
    rescue Moped::Errors::OperationFailure => e
      json_return 200, 'Duplicated FPGAD ID' if e.message.include? 'E11000'
    end

    puts 'New FPGAD has been added'
    response = ''
    case request.content_type
      when 'application/json'
        response = fpga.to_json
      when 'application/x-yaml'
        response = json_to_yaml(fpga.to_json)
      else
        halt 415
    end
    halt 201, {'Content-type' => request.content_type}, response
  end

  # @method update_fpgads
  # @overload put '/fpgads/?'
  # Update a FPGAD by vendor, name and version in JSON or YAML format
  ## Catalogue - UPDATE
  put '/fpgads/?' do
    logger.info "Catalogue: entered PUT /api/v2/fpgads?#{query_string}"

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    # Return if params are empty
    json_error 400, 'Update parameters are null' if keyed_params.empty?

    # Compatibility support for YAML content-type
    case request.content_type
      when 'application/x-yaml'
        # Validate YAML format
        # When updating a FPGAD, the json object sent to API must contain just data inside
        # of the fpgad, without the json field fpgad: before
        fpga, errors = parse_yaml(request.body.read)
        halt 400, errors.to_json if errors

        # Translate from YAML format to JSON format
        new_fpga_json = yaml_to_json(fpga)

        # Validate JSON format
        new_fpga, errors = parse_json(new_fpga_json)
        halt 400, errors.to_json if errors

      else
        # Compatibility support for JSON content-type
        # Parses and validates JSON format
        new_fpga, errors = parse_json(request.body.read)
        halt 400, errors.to_json if errors
    end

    # Validate FPGAD
    # Check if mandatory fields Vendor, Name, Version are included
    json_error 400, 'ERROR: FPGAD Vendor not found' unless new_fpga.has_key?('vendor')
    json_error 400, 'ERROR: FPGAD Name not found' unless new_fpga.has_key?('name')
    json_error 400, 'ERROR: FPGAD Version not found' unless new_fpga.has_key?('version')

    # Set headers
    case request.content_type
      when 'application/x-yaml'
        headers = { 'Accept' => 'application/x-yaml', 'Content-Type' => 'application/x-yaml' }
      else
        headers = { 'Accept' => 'application/json', 'Content-Type' => 'application/json' }
    end
    headers[:params] = params unless params.empty?

    # Retrieve stored version
    if keyed_params[:vendor].nil? && keyed_params[:name].nil? && keyed_params[:version].nil?
      json_error 400, 'Update Vendor, Name and Version parameters are null'
    else
      begin
        fpga = Fpsd.find_by({ 'fpgad.vendor' => keyed_params[:vendor], 'fpgad.name' => keyed_params[:name],
                             'fpgad.version' => keyed_params[:version] })
        puts 'FPGA is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        json_error 404, "The FPGAD Vendor #{keyed_params[:vendor]}, Name #{keyed_params[:name]}, Version #{keyed_params[:version]} does not exist"
      end
    end
    # Check if FPGA already exists in the catalogue by Name, Vendor and Version
    begin
      fpga = Fpsd.find_by({ 'fpgad.name' => new_fpga['name'], 'fpgad.vendor' => new_fpga['vendor'],
                           'fpgad.version' => new_fpga['version'] })
      json_return 200, 'Duplicated FPGAD Name, Vendor and Version'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    if keyed_params.key?(:username)
      username = keyed_params[:username]
    else
      username = nil
    end

    # Update to new version
    puts 'Updating...'
    new_fpgad = {}
    new_fpgad['_id'] = SecureRandom.uuid # Unique UUIDs per FPGAD entries
    new_fpgad['fpgad'] = new_fpga
    new_fpgad['status'] = 'active'
    new_fpgad['signature'] = nil
    new_fpgad['md5'] = checksum new_fpga.to_s
    new_fpgad['username'] = username

    begin
      new_fpga = Fps.create!(new_fpgad)
    rescue Moped::Errors::OperationFailure => e
      json_return 200, 'Duplicated FPGAD ID' if e.message.include? 'E11000'
    end
    logger.debug "Catalogue: leaving PUT /api/v2/fpgads?#{query_string}\" with FPGAD #{new_fpga}"

    response = ''
    case request.content_type
      when 'application/json'
        response = new_fpga.to_json
      when 'application/x-yaml'
        response = json_to_yaml(new_fpga.to_json)
      else
        halt 415
    end
    halt 200, {'Content-type' => request.content_type}, response
  end

  # @method update_fpgads_id
  # @overload put '/catalogues/fpgads/:id/?'
  #	Update a FPGAD by its ID in JSON or YAML format
  ## Catalogue - UPDATE
  put '/fpgads/:id/?' do
    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    unless params[:id].nil?
      logger.debug "Catalogue: PUT /api/v2/fpgads/#{params[:id]}"

      # Transform 'string' params Hash into keys
      keyed_params = keyed_hash(params)

      # Check for special case (:status param == <new_status>)
      if keyed_params.key?(:status)
        logger.info "Catalogue: entered PUT /api/v2/fpgads/#{query_string}"

        # Validate FPGAD
        # Retrieve stored version
        begin
          puts 'Searching ' + params[:id].to_s
          fpga = Fpsd.find_by({ '_id' => params[:id] })
          puts 'FPGAD is found'
        rescue Mongoid::Errors::DocumentNotFound => e
          json_error 404, 'This FPGAD does not exists'
        end

        #Validate new status
        valid_status = %w(active inactive delete)
        if valid_status.include? keyed_params[:status]
          # Update to new status
          begin
            fpga.update_attributes(status: keyed_params[:status])
          rescue Moped::Errors::OperationFailure => e
            json_error 400, 'ERROR: Operation failed'
          end
        else
          json_error 400, "Invalid new status #{keyed_params[:status]}"
        end
        halt 200, "Status updated to {#{query_string}}"

      else
        # Compatibility support for YAML content-type
        case request.content_type
          when 'application/x-yaml'
            # Validate YAML format
            # When updating a FPGAD, the json object sent to API must contain just data inside
            # of the fpgad, without the json field fpgad: before
            fpga, errors = parse_yaml(request.body.read)
            halt 400, errors.to_json if errors

            # Translate from YAML format to JSON format
            new_fpga_json = yaml_to_json(fpga)

            # Validate JSON format
            new_fpga, errors = parse_json(new_fpga_json)
            halt 400, errors.to_json if errors

          else
            # Compatibility support for JSON content-type
            # Parses and validates JSON format
            new_fpga, errors = parse_json(request.body.read)
            halt 400, errors.to_json if errors
        end

        # Validate FPGAD
        # Check if mandatory fields Vendor, Name, Version are included
        json_error 400, 'ERROR: FPGAD Vendor not found' unless new_fpga.has_key?('vendor')
        json_error 400, 'ERROR: FPGAD Name not found' unless new_fpga.has_key?('name')
        json_error 400, 'ERROR: FPGAD Version not found' unless new_fpga.has_key?('version')

        # Retrieve stored version
        begin
          puts 'Searching ' + params[:id].to_s
          fpga = Fpsd.find_by({ '_id' => params[:id] })
          puts 'FPGAD is found'
        rescue Mongoid::Errors::DocumentNotFound => e
          json_error 404, "The FPGAD ID #{params[:id]} does not exist"
        end

        # Check if FPGAD already exists in the catalogue by name, vendor and version
        begin
          fpga = Fpsd.find_by({ 'fpgad.name' => new_fpga['name'], 'fpgad.vendor' => new_fpga['vendor'],
                               'fpgad.version' => new_fpga['version'] })
          json_return 200, 'Duplicated FPGA Name, Vendor and Version'
        rescue Mongoid::Errors::DocumentNotFound => e
          # Continue
        end

        if keyed_params.key?(:username)
          username = keyed_params[:username]
        else
          username = nil
        end

        # Update to new version
        puts 'Updating...'
        new_fpgad = {}
        new_fpgad['_id'] = SecureRandom.uuid # Unique UUIDs per FPGAD entries
        new_fpgad['fpgad'] = new_fpga
        new_fpgad['status'] = 'active'
        new_fpgad['signature'] = nil
        new_fpgad['md5'] = checksum new_fpga.to_s
        new_fpgad['username'] = username

        begin
          new_fpga = Fpsd.create!(new_fpgad)
        rescue Moped::Errors::OperationFailure => e
          json_return 200, 'Duplicated FPGAD ID' if e.message.include? 'E11000'
        end
        logger.debug "Catalogue: leaving PUT /api/v2/fpgads/#{params[:id]}\" with FPGAD #{new_fpga}"

        response = ''
        case request.content_type
          when 'application/json'
            response = new_fpga.to_json
          when 'application/x-yaml'
            response = json_to_yaml(new_fpga.to_json)
          else
            halt 415
        end
        halt 200, {'Content-type' => request.content_type}, response
      end
    end
    logger.debug "Catalogue: leaving PUT /api/v2/fpgads/#{params[:id]} with 'No FPGAD ID specified'"
    json_error 400, 'No FPGAD ID specified'
  end

  # @method delete_fpgads_sp_fpga
  # @overload delete '/fpgads/?'
  #	Delete a FPGAD by vendor, name and version
  delete '/fpgads/?' do
    logger.info "Catalogue: entered DELETE /api/v2/fpgads?#{query_string}"

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    unless keyed_params[:vendor].nil? && keyed_params[:name].nil? && keyed_params[:version].nil?
      begin
        fpga = Fpsd.find_by({ 'fpgad.vendor' => keyed_params[:vendor], 'fpgad.name' => keyed_params[:name],
                             'fpgad.version' => keyed_params[:version] })
        puts 'FPGAD is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        json_error 404, "The FPGAD Vendor #{keyed_params[:vendor]}, Name #{keyed_params[:name]}, Version #{keyed_params[:version]} does not exist"
      end
      logger.debug "Catalogue: leaving DELETE /api/v2/fpgads?#{query_string}\" with FPGAD #{fpga}"
      fpga.destroy
      halt 200, 'OK: FPGAD removed'
    end
    logger.debug "Catalogue: leaving DELETE /api/v2/fpgads?#{query_string} with 'No FPGAD Vendor, Name, Version specified'"
    json_error 400, 'No FPGAD Vendor, Name, Version specified'
  end

  # @method delete_fpgads_sp_fpga_id
  # @overload delete '/catalogues/fpgads/:id/?'
  #	  Delete a FPGAD by its ID
  #	  @param :id [Symbol] id FPGAD ID
  # Delete a FPGAD by uuid
  delete '/fpgads/:id/?' do
    unless params[:id].nil?
      logger.debug "Catalogue: DELETE /api/v2/fpgads/#{params[:id]}"
      begin
        fpga = Fpsd.find(params[:id])
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "The FPGAD ID #{params[:id]} does not exist" unless fpga
      end
      logger.debug "Catalogue: leaving DELETE /api/v2/fpgads/#{params[:id]}\" with FPGAD #{fpga}"
      fpga.destroy
      halt 200, 'OK: FPGAD removed'
    end
    logger.debug "Catalogue: leaving DELETE /api/v2/fpgads/#{params[:id]} with 'No FPGAD ID specified'"
    json_error 400, 'No FPGAD ID specified'
  end
end