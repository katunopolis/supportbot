// Send message endpoint
app.post('/api/chat/:requestId/messages', async (req, res) => {
    const { requestId } = req.params;
    const { message, sender_id, sender_type } = req.body;

    try {
        const apiHost = 'supportbot';
        const apiPort = 8000;

        const options = {
            hostname: apiHost,
            port: apiPort,
            path: `/api/chat/${requestId}/messages`,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const apiRes = await new Promise((resolve, reject) => {
            const req = http.request(options, resolve);
            req.on('error', reject);
            req.write(JSON.stringify({ message, sender_id, sender_type }));
            req.end();
        });

        let data = '';
        await new Promise((resolve, reject) => {
            apiRes.on('data', chunk => data += chunk);
            apiRes.on('end', () => resolve());
            apiRes.on('error', reject);
        });

        if (apiRes.statusCode === 200) {
            res.json(JSON.parse(data));
        } else {
            throw new Error(`API returned status ${apiRes.statusCode}`);
        }
    } catch (error) {
        console.error('Error sending message:', error);
        res.status(500).json({
            error: 'Failed to send message',
            details: error.message
        });
    }
});

// Support request submission endpoint
app.post('/support-request', async (req, res) => {
    console.log('Received support request submission');
    
    try {
        const apiHost = 'supportbot';
        const apiPort = 8000;
        const requestBody = req.body;
        
        console.log('Request body:', requestBody);

        const options = {
            hostname: apiHost,
            port: apiPort,
            path: '/support-request',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        };

        console.log('Proxying support request to supportbot service');
        
        const apiRes = await new Promise((resolve, reject) => {
            const proxyReq = http.request(options, resolve);
            proxyReq.on('error', reject);
            proxyReq.on('timeout', () => {
                proxyReq.destroy();
                reject(new Error('Request timed out'));
            });
            proxyReq.write(JSON.stringify(requestBody));
            proxyReq.end();
        });

        let data = '';
        await new Promise((resolve, reject) => {
            apiRes.on('data', chunk => data += chunk);
            apiRes.on('end', () => resolve());
            apiRes.on('error', reject);
        });

        if (apiRes.statusCode === 200) {
            console.log('Support request submitted successfully');
            res.json(JSON.parse(data));
        } else {
            console.error(`Support request failed with status ${apiRes.statusCode}`);
            throw new Error(`API returned status ${apiRes.statusCode}: ${data}`);
        }
    } catch (error) {
        console.error('Error submitting support request:', error);
        res.status(500).json({
            error: 'Failed to submit support request',
            details: error.message
        });
    }
});

// Start server
app.listen(port, () => {
    console.log(`Web app server running on port ${port}`);
}); 